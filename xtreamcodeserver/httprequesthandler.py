import base64
import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from http import HTTPStatus
import logging
import urllib
import os
from xtreamcodeserver.stream.httpstream import XTreamCodeHTTPStream
from xtreamcodeserver.interfaces.stream import IXTreamCodeStream

_LOGGER = logging.getLogger(__name__)

class XTreamCodeHTTPRequestHandler(BaseHTTPRequestHandler):
    protocol_version = 'HTTP/1.1'

    def __init__(self, xtreamcode_server, allow_all_origin, chunk_size, *args):
        self.m_xtreamcode_server = xtreamcode_server
        self.m_allow_all_origin = allow_all_origin
        self.m_chunk_size = chunk_size
        BaseHTTPRequestHandler.__init__(self, *args)

    def log_message(self, format, *args):
        # _LOGGER.info(format % args)
        return

    def close(self):
        self.close_connection = True  # Request BaseHTTPRequestHandler to close connection

    def __send_response_json(self, http_status_code, reply):
        reply_json = json.dumps(reply)
        reply_json = reply_json.encode('utf-8')
        http_headers = dict()
        http_headers["content-type"] = "application/json"
        http_headers["content-length"] = len(reply_json)

        self.__send_response(http_status_code, http_headers, reply_json)

    def __send_response(self, http_status_code, http_headers, body=None):
        if int(http_status_code) / 100 != 2:
            _LOGGER.warning(
                "%s:%d HTTP RESPONSE ERROR: %s !" % (self.client_address[0], self.client_address[1], http_status_code))

        _LOGGER.debug("%s:%d HTTP RESPONSE: %d (Headers: %s)" % (
            self.client_address[0], self.client_address[1], http_status_code, http_headers))
        # _LOGGER.debug("HTTP BODY: %s" % body)

        BaseHTTPRequestHandler.send_response(self, int(http_status_code))
        self.send_headers(http_headers)

        if body:
            self.wfile.write(body)

    def __send_error(self, http_status_code, message=None):
        _LOGGER.error("%s:%d HTTP RESPONSE ERROR: %s (%s)" % (self.client_address[0], self.client_address[1], http_status_code, message))
        BaseHTTPRequestHandler.send_error(self, int(http_status_code), message)

    def send_headers(self, http_headers):
        http_headers_lower = {k.lower(): v for k, v in http_headers.items()}

        for key in http_headers_lower:
            BaseHTTPRequestHandler.send_header(self, key, http_headers_lower[key])

        if self.m_allow_all_origin:
            if "access-control-allow-origin" not in http_headers_lower:
                self.send_header("access-control-allow-origin", "*")

        BaseHTTPRequestHandler.end_headers(self)

    def get_headers(self):
        return self.headers

    def get_query(self):
        return dict(urllib.parse.parse_qsl(urllib.parse.urlsplit(self.path).query))

    def get_path(self):
        return urllib.parse.urlparse(self.path).path

    def stream(self, stream: IXTreamCodeStream) -> None:
        client_info = "%s:%d" % (self.client_address[0], self.client_address[1])

        _LOGGER.info(f"{client_info} -> Streaming uri -> {stream.get_uri()}")

        total_bytes_sent = 0
        try:
            if stream.open(self.get_path(), self.get_headers()):
                self.send_response(stream.get_http_status_code())
                self.send_headers(stream.get_http_headers())

                while stream.is_opened() and not stream.is_end_of_stream():
                    chunk = stream.read_chunk(chunk_size=self.m_chunk_size)
                    if chunk:
                        total_bytes_sent += len(chunk)
                        try:
                            self.wfile.write(chunk)
                        except (ConnectionAbortedError, ConnectionResetError, IOError) as e:
                            _LOGGER.info(f"{client_info} -> Client disconnected !")
                            break
                        except:
                            _LOGGER.exception(f"{client_info} -> Streaming exception during streaming")
                            break

                if stream.is_end_of_stream():
                    _LOGGER.info(f"{client_info} -> Streaming stopped - Stream reach end of stream (Bytes sent: {total_bytes_sent})")
                elif not stream.is_opened():
                    _LOGGER.warning(f"{client_info} -> Streaming stopped - Stream closed (Bytes sent: {total_bytes_sent})")
            else:
                _LOGGER.error(f"{client_info} -> Unable to open stream: {stream.get_uri()} (Return 404)")
                self.send_error(HTTPStatus.NOT_FOUND)
        except:
            _LOGGER.exception(f"{client_info} -> Unexpected streaming exception")
        finally:
            stream.close()

    def do_GET(self):
        try:
            client_info = "%s:%d" % (self.client_address[0], self.client_address[1])
            range = self.headers.get("range")
           
            # _LOGGER.debug("HTTP GET: %s (Headers: %s)" % (self.path, str(self.headers).split('\n')))
            _LOGGER.info(f"{client_info} HTTP GET: {self.path} (Range: {range})")

            interface_ip = self.request.getsockname()[0]
            query = self.get_query()
            path_splitted = self.get_path().split('/')[1:]
 
            if query.get("u") and not query.get("username"):
                query["username"] = query.get("u")
            if query.get("p") and not query.get("password"):
                query["password"] = query.get("p")

            # Check credentials for /xxxx/username/password/stream_id or get.php?username=username&password=password
            if not self.m_xtreamcode_server.is_credentials_valid(query.get("username"), query.get("password")):
                if not (len(path_splitted) >= 3 and self.m_xtreamcode_server.is_credentials_valid(path_splitted[0], path_splitted[1])):
                    if not (len(path_splitted) >= 3 and self.m_xtreamcode_server.is_credentials_valid(path_splitted[1], path_splitted[2])):
                        return self.__send_error(HTTPStatus.UNAUTHORIZED, "Invalid username/password, inactive or expired !")

            if path_splitted[-1] == "get.php" or path_splitted[-1] == "playlist.m3u":
                m3u_str = self.m_xtreamcode_server.get_m3u(query, interface_ip).encode('utf-8')
                self.__send_response(HTTPStatus.OK,
                                     http_headers={"Content-Disposition": "attachment; filename=\"playlist.m3u\"",
                                                   "Content-Type": "audio/x-mpegurl",
                                                   "Content-Length": len(m3u_str)}, body=m3u_str)

            elif path_splitted[-1] == "player_api.php":
                reply = self.m_xtreamcode_server.invoke_action(query.get("action"), query)
                if reply is None:
                    reply = self.m_xtreamcode_server.get_server_info(query, interface_ip)

                self.__send_response_json(HTTPStatus.OK, reply)

            elif path_splitted[-1] == "xmltv.php":
                reply = self.m_xtreamcode_server.get_xmltv(query, interface_ip).encode('utf-8')
                http_headers = dict()
                http_headers["content-type"] = "application/xml"
                http_headers["content-length"] = len(reply)

                self.__send_response(HTTPStatus.OK, http_headers, reply)

                # Stream file for /proxy/username/password/<base64_url>.ts
            elif path_splitted[0] == "proxy":
                self.stream( XTreamCodeHTTPStream( base64.b64decode(path_splitted[3]).decode("utf-8") + "/" + path_splitted[4] ) )

                # Stream file for /xxxx/username/password/stream_id or /username/password/stream_id
            elif stream := self.m_xtreamcode_server.get_stream(int(os.path.splitext(path_splitted[-1])[0])):
                self.stream( stream )

            else:
                self.__send_error(HTTPStatus.NOT_FOUND, "File not found !")

        except (ConnectionAbortedError, ConnectionResetError) as e:
            _LOGGER.info(f"{client_info} Client disconnected !")
        except:
            _LOGGER.exception(f"{client_info} EXCEPTION while replying to GET")
            self.__send_error(HTTPStatus.INTERNAL_SERVER_ERROR, 'An exception occured !')

        finally:
            self.close()

    def do_POST(self):
        _LOGGER.debug("%s:%d HTTP POST: %s (Headers: %s)" % (
            self.client_address[0], self.client_address[1], self.path, str(self.headers).split('\n')))
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        self.__send_error(HTTPStatus.NOT_IMPLEMENTED)
