import logging
from xtreamcodeserver.interfaces.stream import IXTreamCodeStream
from http import HTTPStatus

_LOGGER = logging.getLogger(__name__)

class XTreamCodeHTTPRedirectStream(IXTreamCodeStream):
    def __init__(self, url):
        self.m_uri = url
        self.m_opened = False

    def get_uri(self) -> str:
        return self.m_uri
    
    def set_uri(self, uri: str) -> None:
        self.m_uri = uri

    def is_available(self):
        return True

    def open(self, http_req_path: str, http_req_headers: dict) -> bool:
        self.m_opened = True
        return True

    def close(self) -> None:
        self.m_opened = False

    def read_chunk(self, chunk_size: int=8192) -> bytes:
        return None

    def is_opened(self) -> bool:
        return self.m_opened

    def is_end_of_stream(self) -> bool:
        return True  # No body, we are end of stream everytime

    def get_http_headers(self) -> dict:
        header = {}
        header["location"] = self.m_uri
        return header

    def get_http_status_code(self) -> HTTPStatus:
        return HTTPStatus.FOUND #Found (Redirection non permanent)
