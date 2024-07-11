import logging
import os
import mimetypes
from xtreamcodeserver.interfaces.stream import IXTreamCodeStream
from http import HTTPStatus

from xtreamcodeserver.utils.http_utils import HTTPUtils

_LOGGER = logging.getLogger(__name__)

#Add few mimetypes not present in default python mimetypes
mimetypes.add_type('video/x-matroska', '.mkv')

class XTreamCodeFileSystemStream(IXTreamCodeStream):
    def __init__(self, file_path: str):
        self.m_uri = file_path
        self.file_fd = None
        self.m_end_of_file = False
        self.m_start_offset = None

    def get_uri(self) -> str:
        return self.m_uri
    
    def set_uri(self, uri: str) -> None:
        self.m_uri = uri

    def is_available(self):
        file_fd = open(self.m_uri, "rb")
        if file_fd:
            file_fd.close()
            return True

        return False

    def open(self, http_req_path: str, http_req_headers: dict) -> bool:
        self.m_start_offset = HTTPUtils.get_start_offset(http_req_headers)

        self.m_end_of_file = False
        self.file_fd = open(self.m_uri, "rb")
        if not self.file_fd:
            _LOGGER.error("Unable to open file: %s" % (self.m_uri))
            return False

        self.file_fd.seek(self.m_start_offset if self.m_start_offset != None else 0)
        return True

    def close(self) -> None:
        if self.file_fd:
            self.file_fd.close()
            self.file_fd = None

    def is_opened(self) -> bool:
        return self.file_fd is not None

    def is_end_of_stream(self) -> bool:
        return self.m_end_of_file

    def read_chunk(self, chunk_size: int=8192) -> bytes:
        ret = self.file_fd.read(chunk_size)
        if len(ret) != chunk_size: #EOF
            self.m_end_of_file = True
        return ret

    def get_http_headers(self) -> dict:
        http_headers = {}
        extension = os.path.splitext(self.m_uri)[1]

        mimetype = "application/octet-stream"  # Default mimetype is octect-stream if it's an unknown type
        if extension in mimetypes.types_map:
            mimetype = mimetypes.types_map[extension]

        total_size = os.path.getsize(self.m_uri)
        current_offset = self.file_fd.tell()

        http_headers["content-type"] = mimetype
        http_headers["content-length"] = total_size - current_offset
        http_headers["content-range"] = "bytes %d-%d/%d" % (current_offset, total_size - 1, total_size)
        http_headers["accept-ranges"] = "0-%d" % total_size

        return http_headers

    def get_http_status_code(self) -> HTTPStatus:
        if self.file_fd is None:
            return HTTPStatus.NOT_ACCEPTABLE

        if self.m_start_offset != None:
            return HTTPStatus.PARTIAL_CONTENT

        return HTTPStatus.OK

    