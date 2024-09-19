from http import HTTPStatus
import requests
import logging
from xtreamcodeserver.interfaces.stream import IXTreamCodeStream

_LOGGER = logging.getLogger(__name__)

LOG_HEADERS = False

class XTreamCodeHTTPStream(IXTreamCodeStream):
    def __init__(self, url: str, max_retry: int=3):
        self.m_uri = url
        self.m_req_headers = {}
        self.m_rsp_header = {}
        self.m_max_retry = max_retry
        self.m_resp = None
        self.m_is_live = False
        self.m_byte_received = 0

    def get_uri(self) -> str:
        if self.m_resp != None:
            return self.m_resp.url
        
        return self.m_uri
    
    def set_uri(self, uri: str) -> None:
        self.m_uri = uri

    def is_available(self) -> bool:
        stream_alive = False

        resp = self.__open(timeout_connect_read=2)
        if resp:
            if next(resp.iter_content(128)):
                stream_alive = True
            else:
                _LOGGER.warning("'%s' is down (No data received !)" % self.m_uri)

        if resp:
            resp.close()

        #_LOGGER.debug("Media HTTP '%s' available: %s" % (self.m_uri, "True" if stream_alive else "False"))

        return stream_alive

    def open(self, http_req_path: str, http_req_headers: dict) -> bool:
        req_headers = {}
        for key, value in http_req_headers.items():
            req_headers[key.lower()] = value
        req_headers.pop("host", None)  # Remove original header and let requests provide the correct "host"
        
        self.m_byte_received = 0
        self.m_req_headers = req_headers

        #Timeout must be bigger than 2 seconds, because the server can take a while to respond during live streaming
        self.m_resp = self.__open(req_headers, priority=1, timeout_connect_read=30)
        if self.m_resp:

            self.m_rsp_header = {}
            for header in self.m_resp.headers.items():
                self.m_rsp_header[header[0].lower()] = header[1]

            self.m_is_live = "content-length" not in self.m_rsp_header  # If the stream is live, the content-length is not provided, thus we need to use chunked transfer encoding 
            #_LOGGER.debug("HTTPStream: Stream is live: %s" % ("True" if self.m_is_live else "False"))

            # Forward the response
            self.m_rsp_header.pop("date", None)  # Will be automatically added by the self.end_headers()
            self.m_rsp_header.pop("server", None)  # Will be automatically added by the self.end_headers()
            self.m_rsp_header.pop("transfer-encoding", None)  # Because of stream=True, the "requests.get" will add transfer-encoding, but we don't except to send back data as chunked, thus remove this header

            return True

        return False

    def close(self) -> None:
        if self.m_resp:
            self.m_resp.close()
            self.m_resp = None

        self.m_rsp_header = {}

    def read_chunk(self, chunk_size: int=8192) -> bytes:

        for i in range (0, self.m_max_retry):

            if not self.is_opened(): # If the stream is live, we need to retry to open the stream
                if not self.m_is_live:
                    break

                _LOGGER.warning("HTTPStream: Retrying to open live stream '%s' (Retry: %d/%d)" % (self.m_uri, i, self.m_max_retry))
                self.close()
                self.open(None, self.m_req_headers)

            try:
                # _LOGGER.debug("HTTPStream: Waiting for iteration (Chunk: %d)..." % (chunk_size))
                ret = next(self.m_resp.iter_content(chunk_size))
                if ret:
                    self.m_byte_received += len(ret)
                    return ret

                _LOGGER.debug(f"HTTPStream: End of stream (Bytes received: {self.m_byte_received}) !")
                break #Normal case, end of stream
            except StopIteration:
                _LOGGER.debug(f"HTTPStream: End of stream (Bytes received: {self.m_byte_received}) !")
                break  #Normal case, end of stream
            except requests.exceptions.StreamConsumedError:
                _LOGGER.error(f"HTTPStream: URL stream error: '{self.m_uri}'")
            except (requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout):
                _LOGGER.error(f"HTTPStream: timeout for URL: '{self.m_uri}'")
            except requests.exceptions.ConnectionError:
                _LOGGER.error(f"HTTPStream: Connection error: '{self.m_uri}' (Probably caused by resp.close())")
            except:
                _LOGGER.exception(f"HTTPStream: exception for url: '{self.m_uri}'")

        self.close()
        return None
    
    def is_end_of_stream(self) -> bool:
        return self.m_resp == None

    def is_opened(self) -> bool:
        return (self.m_resp is not None) and (int(self.m_resp.status_code / 100) == 2)

    def get_http_headers(self) -> dict:
        return self.m_rsp_header

    def get_http_status_code(self) -> HTTPStatus:
        if self.m_resp is None:
            return HTTPStatus.NOT_ACCEPTABLE

        return self.m_resp.status_code
    
    @staticmethod
    def __log_headers(header_type: str, headers: dict) -> None:
        if LOG_HEADERS:
            _LOGGER.debug("******************** Headers %s ********************" % header_type)
            for key, value in headers.items():
                _LOGGER.debug("%s: %s" % (key, value))
            _LOGGER.debug("******************************************************")
        
    def __open(self, http_req_headers: str=None, priority: int=0, timeout_connect_read: int=2) -> requests.Response:
        XTreamCodeHTTPStream.__log_headers("Req", http_req_headers)
        resp = requests.request("GET", self.m_uri, headers=http_req_headers, stream=True, timeout=timeout_connect_read)
        if resp and (int(resp.status_code / 100) == 2):
            XTreamCodeHTTPStream.__log_headers("Res", resp.headers)
            return resp

        if resp:
            resp.close()

        return None
