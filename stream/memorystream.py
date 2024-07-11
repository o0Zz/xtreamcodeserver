import logging
from xtreamcodeserver.interfaces.stream import IXTreamCodeStream
from http import HTTPStatus

from xtreamcodeserver.utils.http_utils import HTTPUtils

_LOGGER = logging.getLogger(__name__)

class XTreamCodeMemoryStream(IXTreamCodeStream):
    def __init__(self, data: bytearray, mimetype: str, url: str=None):
        self.m_data = data
        self.m_mimetype = mimetype
        self.m_url = url
        self.m_offset = 0
        self.m_opened = False
        self.m_http_status = HTTPStatus.OK
        self.m_http_headers = {}

        if self.m_url is None:
            self.m_url = "memory://" + str(id(self))

    def get_uri(self) -> str:
        return self.m_url
    
    def set_uri(self, uri: str) -> None:
        self.m_url = uri

    def is_available(self):
        return True

    def open(self, http_req_path: str, http_req_headers: dict) -> bool:
        start_offset = HTTPUtils.get_start_offset(http_req_headers)
        
        self.m_offset = 0
        if start_offset is not None:
            self.m_offset = start_offset
        
        if self.m_offset != 0:
            self.m_http_status = HTTPStatus.PARTIAL_CONTENT

        self.m_http_headers = {}
        total_size = len(self.m_data)
        self.m_http_headers["content-type"] = self.m_mimetype
        self.m_http_headers["content-length"] = len(self.m_data) - self.m_offset
        self.m_http_headers["content-range"] = "bytes %d-%d/%d" % (self.m_offset, len(self.m_data) - 1, len(self.m_data))
        self.m_http_headers["accept-ranges"] = "0-%d" % len(self.m_data)

        self.m_opened = True
        return True

    def is_opened(self) -> bool:
        return self.m_opened

    def is_end_of_stream(self) -> bool:
        if not self.m_opened:
            return True
        
        return self.m_offset >= len(self.m_data)

    def close(self) -> None:
        self.m_opened = False

    def read_chunk(self, chunk_size: int=8192) -> bytes:
        if not self.m_opened:
            return None
        
        ret = self.m_data[self.m_offset:self.m_offset + chunk_size]
        self.m_offset += len(ret)
        return ret

    def get_http_headers(self) -> dict:
        return self.m_http_headers

    def get_http_status_code(self) -> HTTPStatus:
        return self.m_http_status
