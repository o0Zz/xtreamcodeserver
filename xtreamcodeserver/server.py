import datetime
import threading
import time
from http.server import HTTPServer
import logging
import urllib
from datetime import timezone
import base64
from socketserver import ThreadingMixIn
from xtreamcodeserver.interfaces.proxyregistry import IXTreamCodeProxyRegistry
from xtreamcodeserver.credentials.credentials import XTreamCodeCredentials
from xtreamcodeserver.entry.category import XTreamCodeCategory
from xtreamcodeserver.httprequesthandler import XTreamCodeHTTPRequestHandler
from xtreamcodeserver.entry.entry import XTreamCodeType
from xtreamcodeserver.interfaces.datetimeprovider import IXTreamCodeDateTimeProvider
from xtreamcodeserver.interfaces.epgprovider import IXTreamCodeEPGProvider
from xtreamcodeserver.interfaces.credentialsprovider import IXTreamCodeCredentialsProvider
from xtreamcodeserver.interfaces.entryprovider import IXTreamCodeEntryProvider

_LOGGER = logging.getLogger(__name__)

def xml_escape(data):
    if data:
        data = data.replace("&", "&amp;")
        data = data.replace(">", "&gt;")
        data = data.replace("<", "&lt;")

    return data
    
class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """Handle requests in a separate thread, with a hard cap on concurrent connections."""

    daemon_threads = True
    request_queue_size = 64

    def __init__(self, server_address, request_handler_class, max_concurrent_connections: int = 0):
        self.m_connection_semaphore = None
        if max_concurrent_connections and max_concurrent_connections > 0:
            self.m_connection_semaphore = threading.BoundedSemaphore(max_concurrent_connections)
        HTTPServer.__init__(self, server_address, request_handler_class)

    def process_request(self, request, client_address):
        if self.m_connection_semaphore is not None and not self.m_connection_semaphore.acquire(blocking=False):
            # Too many connections: drop the new one instead of spawning yet another thread
            _LOGGER.warning(f"{client_address[0]}:{client_address[1]} -> Connection refused (Max concurrent connections reached)")
            self.shutdown_request(request)
            return

        try:
            ThreadingMixIn.process_request(self, request, client_address)
        except Exception:
            self.__release_connection()
            raise

    def process_request_thread(self, request, client_address):
        try:
            ThreadingMixIn.process_request_thread(self, request, client_address)
        finally:
            self.__release_connection()

    def __release_connection(self):
        if self.m_connection_semaphore is not None:
            try:
                self.m_connection_semaphore.release()
            except ValueError:
                pass


class _AuthThrottle:
    """Per client IP lock-out after too many failed logins (brute-force protection)."""

    def __init__(self, max_failures: int, lockout_seconds: int):
        self.m_lock = threading.Lock()
        self.m_max_failures = max_failures
        self.m_lockout_seconds = lockout_seconds
        self.m_clients = {}  # ip -> [failure_count, window_start, locked_until]

    def is_enabled(self) -> bool:
        return self.m_max_failures > 0 and self.m_lockout_seconds > 0

    def is_locked(self, client_ip: str) -> bool:
        if not self.is_enabled():
            return False

        now = time.monotonic()
        with self.m_lock:
            state = self.m_clients.get(client_ip)
            if state is None:
                return False

            if state[2] > now:
                return True

            if state[1] + self.m_lockout_seconds < now:  # Window expired, forget it
                self.m_clients.pop(client_ip, None)

            return False

    def record_failure(self, client_ip: str) -> None:
        if not self.is_enabled():
            return

        now = time.monotonic()
        with self.m_lock:
            state = self.m_clients.get(client_ip)
            if state is None or state[1] + self.m_lockout_seconds < now:
                state = [0, now, 0.0]
                self.m_clients[client_ip] = state

            state[0] += 1
            if state[0] >= self.m_max_failures:
                state[2] = now + self.m_lockout_seconds
                _LOGGER.warning(f"{client_ip} -> Locked out for {self.m_lockout_seconds}s after {state[0]} failed login attempts")

            if len(self.m_clients) > 10000:  # Bound memory: purge expired entries
                for ip in [ip for ip, s in self.m_clients.items() if s[2] <= now and s[1] + self.m_lockout_seconds < now]:
                    self.m_clients.pop(ip, None)

    def record_success(self, client_ip: str) -> None:
        if not self.is_enabled():
            return

        with self.m_lock:
            state = self.m_clients.get(client_ip)
            if state is not None and state[2] <= time.monotonic():
                self.m_clients.pop(client_ip, None)

class XTreamCodeDefaultDateTimeProvider(IXTreamCodeDateTimeProvider):
    def utcnow(self):
        return datetime.datetime.now(timezone.utc)

class XTreamCodeServer(threading.Thread):

    def __init__(self, entry_provider: IXTreamCodeEntryProvider, epg_provider: IXTreamCodeEPGProvider, credentials_provider: IXTreamCodeCredentialsProvider, proxy_registry: IXTreamCodeProxyRegistry, datetime_provider: IXTreamCodeDateTimeProvider=None):
        """
        entry_provider: categories / streams served by this server.
        epg_provider: EPG data (may be None).
        credentials_provider: accounts allowed to connect (None: no authentication).
        proxy_registry: token <-> upstream URL registry backing the /proxy/ route. Pass the very same
            instance to every XTreamCodePlaylistProxyStream served by this server.
        datetime_provider: clock (default: UTC now).
        """
        threading.Thread.__init__(self)

        if proxy_registry is None:
            raise ValueError("XTreamCodeServer requires a proxy registry (e.g. XTreamCodeProxyMemoryRegistry)")

        self.m_bind_addr = "0.0.0.0"
        self.m_bind_port = 8081
        self.m_external_url = None
        self.m_timezone = timezone.utc
        self.m_allow_all_origin = True
        self.m_http_server = None
        self.m_is_running = False
        self.m_chunk_size = 1024 * 1024 
        self.m_max_concurrent_connections = 200
        self.m_request_timeout_seconds = 30
        self.m_auth_throttle = _AuthThrottle(max_failures=10, lockout_seconds=300)
        self.m_proxy_registry = proxy_registry
        self.m_stream_slots_lock = threading.Lock()
        self.m_stream_slots = {}  # username -> active stream count
        self.m_credentials_provider = credentials_provider
        self.m_entry_provider = entry_provider
        self.m_epg_provider = epg_provider
        self.m_datetime_provider = datetime_provider
        
        if self.m_datetime_provider is None:
            self.m_datetime_provider = XTreamCodeDefaultDateTimeProvider()
        
        self.m_actions = {
            "get_live_categories": self.get_live_categories,
            "get_vod_categories": self.get_vod_categories,
            "get_series_categories": self.get_series_categories,
            "get_live_streams": self.get_live_streams,
            "get_vod_streams": self.get_vod_streams,
            "get_series": self.get_series,
            "get_series_info": self.get_series_info,
            "get_vod_info": self.get_vod_info,
            "get_short_epg": self.get_short_epg,
            "get_simple_data_table": self.get_simple_data_table
        }

    # ------------------------------------------------------------

    def get_base_url(self, query: dict=None, interface_ip: str=None):
        #Handle reverse proxy case
        if (query is not None) and ("X-Forwarded-Host" in query) and ("X-Forwarded-Proto" in query):
            requested_host = query.get("X-Forwarded-Proto") + "://" + query.get("X-Forwarded-Host")
            if "X-Forwarded-Port" in query:
                requested_host += ":" + query.get("X-Forwarded-Port")
            return requested_host
        
        if self.m_external_url:
            return self.m_external_url

        if interface_ip is None:
            interface_ip = self.m_bind_addr

        return f"http://{interface_ip}:{self.m_bind_port}"
    
    # ------------------------------------------------------------

    def is_credentials_valid(self, username: str, password: str) -> bool:
        authenticated, _credentials = self.authenticate(username, password)
        return authenticated

    # ------------------------------------------------------------

    def authenticate(self, username: str, password: str) -> tuple[bool, XTreamCodeCredentials]:
        """Returns (authenticated, credentials). credentials is None when no provider is configured."""
        if self.m_credentials_provider is None:
            return True, None

        if username is None or password is None:
            return False, None

        credential = self.m_credentials_provider.get_credentials(username, password)
        if credential is None:
            return False, None

        if not credential.is_active(self.m_datetime_provider.utcnow()):
            return False, None

        return True, credential

    # ------------------------------------------------------------

    def is_client_locked_out(self, client_ip: str) -> bool:
        return self.m_auth_throttle.is_locked(client_ip)

    def on_authentication_failed(self, client_ip: str) -> None:
        self.m_auth_throttle.record_failure(client_ip)

    def on_authentication_succeeded(self, client_ip: str) -> None:
        self.m_auth_throttle.record_success(client_ip)

    # ------------------------------------------------------------

    def acquire_stream_slot(self, credentials: XTreamCodeCredentials) -> bool:
        """Enforce credentials.max_connections (<= 0 or None means unlimited)."""
        if credentials is None:
            return True

        max_connections = credentials.get_max_connections()
        if max_connections is None or max_connections <= 0:
            return True

        username = credentials.get_username()
        with self.m_stream_slots_lock:
            current = self.m_stream_slots.get(username, 0)
            if current >= max_connections:
                return False
            self.m_stream_slots[username] = current + 1

        return True

    def release_stream_slot(self, credentials: XTreamCodeCredentials) -> None:
        if credentials is None:
            return

        max_connections = credentials.get_max_connections()
        if max_connections is None or max_connections <= 0:
            return

        username = credentials.get_username()
        with self.m_stream_slots_lock:
            current = self.m_stream_slots.get(username, 0)
            if current <= 1:
                self.m_stream_slots.pop(username, None)
            else:
                self.m_stream_slots[username] = current - 1

    def get_active_stream_count(self, username: str) -> int:
        with self.m_stream_slots_lock:
            return self.m_stream_slots.get(username, 0)


    # ------------------------------------------------------------
    
    def run(self) -> None:
        self.m_is_running = True

        def _http_request_handler(*args):
            XTreamCodeHTTPRequestHandler(self, self.m_proxy_registry, self.m_allow_all_origin, self.m_chunk_size, self.m_request_timeout_seconds, *args)

        self.m_http_server = ThreadedHTTPServer((self.m_bind_addr, self.m_bind_port), _http_request_handler, self.m_max_concurrent_connections)

        _LOGGER.info(f"XTreamcode server started ! (Listening on {self.m_bind_addr}:{self.m_bind_port})")
        self.m_http_server.serve_forever()

        self.m_is_running = False

    # ------------------------------------------------------------
        
    def setup(self, bind_addr: str="0.0.0.0", bind_port: int=8081, external_url: str=None, allow_all_origin: bool=True, timezone: timezone=timezone.utc, chunk_size: int=1024 * 1024,
              max_concurrent_connections: int=200, request_timeout_seconds: int=30, max_auth_failures: int=10, auth_lockout_seconds: int=300) -> None:
        """
        max_concurrent_connections: hard cap on simultaneous client connections (<= 0: unlimited).
        request_timeout_seconds: socket timeout while reading a request (slowloris protection, <= 0: none).
        max_auth_failures / auth_lockout_seconds: a client IP is locked out for auth_lockout_seconds after
            max_auth_failures failed logins within that window (<= 0 disables).
        """
        self.m_bind_addr = bind_addr
        self.m_bind_port = bind_port
        self.m_external_url = external_url
        self.m_timezone = timezone
        self.m_allow_all_origin = allow_all_origin
        self.m_chunk_size = chunk_size
        self.m_max_concurrent_connections = max_concurrent_connections
        self.m_request_timeout_seconds = request_timeout_seconds if (request_timeout_seconds and request_timeout_seconds > 0) else None
        self.m_auth_throttle = _AuthThrottle(max_failures=max_auth_failures, lockout_seconds=auth_lockout_seconds)

    # ------------------------------------------------------------

    def start(self) -> None:
        _LOGGER.info("Starting XTreamcode server ...")
        threading.Thread.start(self)

    # ------------------------------------------------------------

    def is_running(self) -> bool:
        return self.m_is_running

    # ------------------------------------------------------------

    def stop(self) -> None:
        _LOGGER.info("Stopping XTreamcode server ...")

        if self.m_http_server is not None:
            self.m_http_server.shutdown()

        self.join()

        _LOGGER.info("XTreamcode server stopped")

    # ------------------------------------------------------------

    def invoke_action(self, action: str, query: dict) -> dict:
        if action in self.m_actions:
            return self.m_actions[action](query)
        
        if action is not None:
            _LOGGER.error(f"Unexpected action: {action}")
            
        return None

    # ------------------------------------------------------------

    def get_stream(self, entry_id: int):
        stream_entry = self.m_entry_provider.get_entry(entry_id)
        if stream_entry is not None:
            # Entries hold a single shared stream instance, but the server is
            # multi-threaded and a single client commonly opens several concurrent
            # connections (probe + playback + range requests) to the same entry.
            # Hand each request its own clone so they don't race on shared
            # per-request state (file descriptors, offsets, ffmpeg processes).
            stream = stream_entry.get_stream()
            return stream.clone() if stream is not None else None

        return None
    
    # ------------------------------------------------------------

    def get_json_epg(self, stream_id: int, limit: int, simple_data_table: bool) -> dict:
        ret = []

        entry = self.m_entry_provider.get_entry(stream_id)
        if not entry or entry.get_type() != XTreamCodeType.LIVE:
            _LOGGER.error(f"get_short_epg: Invalid stream_id: {stream_id} (Doesn't exist or is not Live) !")
            return {"epg_listings": ret}

        if self.m_epg_provider is None:
            _LOGGER.error("get_short_epg: EPG provider is not set !")
            return {"epg_listings": ret}
        
        epg_channel = self.m_epg_provider.get_channel(entry.get_epg_channel_id())
        
        date_time_now = self.m_datetime_provider.utcnow()

        for programme in epg_channel.get_programme_list():
            if programme.get_datetime_stop_utc().timestamp() >= date_time_now.timestamp():

                epg_start_tz = programme.get_datetime_start_utc().astimezone(tz=self.m_timezone)
                epg_stop_tz = programme.get_datetime_stop_utc().astimezone(tz=self.m_timezone)
                epg_programme = {
                    "id": "0",  # TODO
                    "epg_id": "0",
                    "title": base64.b64encode(programme.get_title().encode('utf-8')).decode('utf-8'),
                    "lang": "",
                    "start": epg_start_tz.strftime("%Y-%m-%d %H:%M:%S"),  # .astimezone(tz=self.m_timezone)
                    "end": epg_stop_tz.strftime("%Y-%m-%d %H:%M:%S"),  # .astimezone(tz=self.m_timezone)
                    "description": base64.b64encode(programme.get_desc().encode('utf-8')).decode('utf-8'),
                    "channel_id": entry.get_epg_channel_id(),
                    "start_timestamp": str(int(programme.get_datetime_start_utc().timestamp())),
                    "stop_timestamp": str(int(programme.get_datetime_stop_utc().timestamp())),
                }

                if simple_data_table:
                    epg_programme["now_playing"] = 0 if epg_start_tz.timestamp() > date_time_now.timestamp() else 1
                    epg_programme["has_archive"] = 0
                else:
                    epg_programme["stream_id"] = str(entry.get_entry_id())

                ret.append(epg_programme)

                if limit != 0 and len(ret) >= limit:
                    break

        return {"epg_listings": ret}

    # ------------------------------------------------------------

    def get_short_epg(self, query: dict) -> dict:
        stream_id = int(query.get("stream_id"))
        limit = 4
        if "limit" in query:
            limit = int(query.get("limit"))

        return self.get_json_epg(stream_id, limit, False)
    
    # ------------------------------------------------------------

    def get_simple_data_table(self, query: dict) -> list[dict]:
        stream_id = int(query.get("stream_id"))
        return self.get_json_epg(stream_id, 0, True)
    
    # ------------------------------------------------------------

    # XMLTV must be as small as possible or it will break some applications like SmartersPlayer
    def get_xmltv(self, query: dict, interface_ip: str) -> str:
        buffer_line = ['<?xml version="1.0" encoding="utf-8" ?>',
                       '<!DOCTYPE tv SYSTEM "xmltv.dtd">',
                       f'<tv generator-info-name="pyXTreamCodeServer" generator-info-url="{self.get_base_url(query, interface_ip)}">']

        date_time_now = self.m_datetime_provider.utcnow()
        list_of_channel_id = []
        entries = self.m_entry_provider.get_entries(category_type=XTreamCodeType.LIVE)
        for entry in entries:
            if entry.get_epg_channel_id():
                if entry.get_epg_channel_id() not in list_of_channel_id:
                    list_of_channel_id.append(entry.get_epg_channel_id())

        epg_channels = []
        if self.m_epg_provider is not None:
            epg_channels = self.m_epg_provider.get_channels()

        for channelid, channel in epg_channels:
            if channelid in list_of_channel_id:  # Only include known channels
                buffer_line.append('<channel id="%s"><display-name>%s</display-name><icon src="%s"/></channel>' % \
                                    (channel.get_channel_id(), xml_escape(channel.get_display_name()),
                                    channel.get_cover_url()))

        for channelid, channel in epg_channels:
            if channelid in list_of_channel_id:  # Only include known channels
                for programme in channel.get_programme_list():
                    if programme.get_datetime_stop_utc().timestamp() >= date_time_now.timestamp():  # Only include programme in future and remove past ones
                        buffer_line.append(
                            '<programme start="%s" stop="%s" channel="%s"><title>%s</title><desc>%s</desc></programme>' % \
                            (programme.get_datetime_start_utc().strftime("%Y%m%d%H%M%S"),
                                programme.get_datetime_stop_utc().strftime("%Y%m%d%H%M%S"),
                                channel.get_channel_id(),
                                xml_escape(programme.get_title()),
                                xml_escape(programme.get_desc())))

        buffer_line.append('</tv>')
        buffer_str = '\n'.join(buffer_line)

        return buffer_str

    # ------------------------------------------------------------

    def get_m3u(self, query: dict, interface_ip: str) -> str:
        m3u_line = ["#EXTM3U"]

        default_output_container = "ts"
        if "output" in query:
            default_output_container = query.get("output")
        
        category_type = None
        if "filter" in query:
            if query.get("filter") == "serie":
                category_type = XTreamCodeType.SERIE
            elif query.get("filter") == "vod":
                category_type = XTreamCodeType.VOD
            elif query.get("filter") == "live":
                category_type = XTreamCodeType.LIVE

        category_id = None
        if "category_id" in query:
            category_id = int(query.get("category_id"))
                
        entries = self.m_entry_provider.get_entries(category_type=category_type)
        for entry in entries:

            if category_id is not None and entry.get_category_id() != category_id:
                continue

            category = self.m_entry_provider.get_category(entry.get_category_id())

            entries = [entry]
            if entry.get_type() == XTreamCodeType.SERIE: 
                entries = entry.get_all_episodes()
            
            for entry in entries:
                container_ext = default_output_container
                epg_channel_id=""

                if entry.get_type() == XTreamCodeType.LIVE:
                    epg_channel_id = entry.get_epg_channel_id()

                if entry.get_type() == XTreamCodeType.VOD or entry.get_type() == XTreamCodeType.EPISODE:
                    container_ext = entry.get_container_extension()
                
                m3u_line.append('#EXTINF:-1 tvg-ID="%s" tvg-name="%s" tvg-logo="%s" group-title="%s",%s' % (epg_channel_id, 
                                                                                                            entry.get_name(), 
                                                                                                            entry.get_cover_url() if entry.get_cover_url() else "", 
                                                                                                            category.get_name() if category else "", 
                                                                                                            entry.get_name()))
                m3u_line.append("%s/%s/%s/%d.%s" % (self.get_base_url(query, interface_ip),
                                                    query.get("username"),
                                                    query.get("password"),
                                                    entry.get_entry_id(),
                                                    container_ext))

        return '\n'.join(m3u_line)

    # ------------------------------------------------------------

    def get_vod_categories(self, query: dict) -> list[XTreamCodeCategory]:
        return self.m_entry_provider.get_categories(XTreamCodeType.VOD)

    # ------------------------------------------------------------

    def get_series_categories(self, query: dict) -> list[XTreamCodeCategory]:
        return self.m_entry_provider.get_categories(XTreamCodeType.SERIE)

    # ------------------------------------------------------------

    def get_live_categories(self, query: dict) -> list[XTreamCodeCategory]:
        return self.m_entry_provider.get_categories(XTreamCodeType.LIVE)

    # ------------------------------------------------------------

    def get_streams(self, category_type: XTreamCodeType, query: dict) -> list[dict]:
        stream_list_json = []

        category_id = query.get("category_id")
        if category_id == "*":
            category_id = None

        entries = self.m_entry_provider.get_entries(category_type=category_type, category_id=category_id)
        for i in range(0, len(entries)):
            if category_type == XTreamCodeType.SERIE:
                stream_list_json.append(entries[i].get_serie_json(i + 1))
            else:
                stream_list_json.append(entries[i].get_streams_json(i + 1))
        return stream_list_json

    # ------------------------------------------------------------

    def get_live_streams(self, query: dict) -> list[dict]:
        return self.get_streams(XTreamCodeType.LIVE, query)

    # ------------------------------------------------------------

    def get_vod_streams(self, query: dict) -> list[dict]:
        return self.get_streams(XTreamCodeType.VOD, query)

    # ------------------------------------------------------------

    def get_series(self, query: dict) -> list[dict]:
        return self.get_streams(XTreamCodeType.SERIE, query)

    # ------------------------------------------------------------

    def get_series_info(self, query: dict) -> list[dict]:
        serie_entry = self.m_entry_provider.get_entry(query.get("series_id"))
        if serie_entry:
            return serie_entry.get_serie_info_json()
        return []

    # ------------------------------------------------------------

    def get_vod_info(self, query: dict) -> list[dict]:
        vod_entry = self.m_entry_provider.get_entry(query.get("vod_id"))
        if vod_entry:
            return vod_entry.get_info_json()
        return []

    # ------------------------------------------------------------

    def get_server_info(self, query: dict, interface_ip: str) -> dict:
        date_now = self.m_datetime_provider.utcnow()

        url_parsed = urllib.parse.urlparse(self.get_base_url(query, interface_ip))
        port = url_parsed.port
        if port is None:
            port=80
            if url_parsed.scheme == "https":
                port=443

        credentials = XTreamCodeCredentials(None, None)
        if self.m_credentials_provider is not None:
            credentials = self.m_credentials_provider.get_credentials(query.get("username"), query.get("password"))
        
        dict = {
            "user_info": {
                "username": credentials.get_username(),
                "password": credentials.get_password(),
                "message": "",
                "auth": 1,
                "status": "Active" if credentials.is_active(date_now) else "Inactive",
                "is_trial": 0,
                "active_cons": 0,
                "created_at": 0, # Time in seconds since epoch time
                "max_connections": credentials.get_max_connections(),
                "allowed_output_formats": ["m3u8", "ts"]  # "rtmp" << Not supported yet
            },
            "server_info": {
                "url": url_parsed.hostname,
                "port": str(port),
                "https_port": str(port),
                "server_protocol": str(url_parsed.scheme),
                "rtmp_port": "0",  # Not support (server_protocol have to be http or https)
                "timezone": "GMT",
                "timestamp_now": int(date_now.timestamp()),
                "time_now": date_now.strftime('%Y-%m-%d %H:%M:%S')
            }
        }

        if credentials.get_expiration_date() is not None:
            dict["user_info"]["exp_date"] = int(credentials.get_expiration_date().timestamp()) # Time in seconds since epoch time

        return dict

