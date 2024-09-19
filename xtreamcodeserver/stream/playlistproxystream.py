import base64
import logging
import os
import urllib
from http import HTTPStatus

from xtreamcodeserver.interfaces.stream import IXTreamCodeStream

_LOGGER = logging.getLogger(__name__)

# URL provided by server is:
# http://127.0.0.1:8081/username/password/1383663399
# However, the URL that should be used is:
# http://127.0.0.1:8081/live/username/password/1383663399.ts
# http://127.0.0.1:8081/live/username/password/1383663399.m3u8

class XTreamCodePlaylistProxyStream(IXTreamCodeStream):
    def __init__(self, stream: IXTreamCodeStream, override_stream_ext: bool=False, memorize_m3u8_redirection: bool=True):
        self.m_stream = stream
        self.m_override_stream_ext = override_stream_ext
        self.m_original_uri = self.m_stream.get_uri()
        self._content = None
        self.m_ext_x_media_sequence = 0
        self.m_last_server_hostname = None
        self.m_memorize_m3u8_redirection = memorize_m3u8_redirection
        self.m_redirected_m3u8_uri = None

    def get_uri(self) -> str:
        return self.m_stream.get_uri()
    
    def set_uri(self, uri: str) -> None:
        self.m_stream.set_uri(uri)
        self.m_original_uri = uri

    def is_available(self) -> bool:
        if self._content is not None:
            return True
        
        return self.m_stream.is_available()

    #Ask player to redirect itself to 
    def open(self, http_req_path: str, http_req_headers: dict) -> bool:
        http_req_path_wo_ext, http_req_extension = os.path.splitext(http_req_path)
        original_uri_wo_ext, original_uri_extension = os.path.splitext(self.m_original_uri)
        stream_extension = original_uri_extension
        if self.m_override_stream_ext:
            stream_extension = http_req_extension

        self.m_stream.set_uri(original_uri_wo_ext + stream_extension)

        redirection = "None"
        if (http_req_extension == ".m3u8") and (self.m_redirected_m3u8_uri is not None):
            self.m_stream.set_uri(self.m_redirected_m3u8_uri)
            redirection = self.m_redirected_m3u8_uri
            self.m_redirected_m3u8_uri = None
        
        _LOGGER.debug(f"XTreamCode Stream Opening {original_uri_wo_ext + stream_extension} (Redirect: {redirection})")
        
        ret = self.m_stream.open(http_req_path, http_req_headers)
        if (ret == True) and (http_req_extension == ".m3u8"):
            self._content = self.__proxify_m3u8(http_req_path)
            if self._content is None:
                self.m_stream.close()
                ret = False

            if self.m_memorize_m3u8_redirection:
                self.m_redirected_m3u8_uri = self.m_stream.get_uri()

        return ret
    
    def close(self) -> None:
        self.m_stream.close()
        self._content = None

    def read_chunk(self, chunk_size: int=8192) -> bytes:
        if self._content is not None:
            ret = self._content
            self._content = None
            return ret
        
        return self.m_stream.read_chunk(chunk_size=chunk_size)

    def is_end_of_stream(self) -> bool:
        if self._content is not None:
            return False
        
        return self.m_stream.is_end_of_stream()

    def is_opened(self) -> bool:
        return self.m_stream.is_opened()

    def get_http_headers(self) -> dict:
        headers = self.m_stream.get_http_headers()
        if self._content is not None:
            headers["content-length"] = str(len(self._content))
            headers.pop("content-range", None)
            headers.pop("accept-ranges", None)
        return headers
    
    def get_http_status_code(self) -> HTTPStatus:
        return self.m_stream.get_http_status_code()
    
    def __proxify_m3u8(self, http_req_path: str) -> None:
        content = ""
        m3u8_data = self.m_stream.read_chunk(chunk_size=128*1024) #read the whole m3u8 file
        if m3u8_data is None:
            return None

        ext_x_media_sequence = 0
        for line in m3u8_data.splitlines():  
            str = line.decode("utf-8")
            if str == "":
                continue
            
            if str[0] == "#":
                if str.startswith("#EXT-X-MEDIA-SEQUENCE:"):
                    ext_x_media_sequence = int(str.split(":")[1])
                content += str + "\n"
                continue

            url_parsed = urllib.parse.urlparse(self.m_stream.get_uri())
            path_without_filename, filename_with_ext = os.path.split(str)

            #http req path will look like /xxxx/user/password/xxxx.m3u8
            http_req_path_splitted = http_req_path.split('/')[1:]
            username = http_req_path_splitted[-3]
            password = http_req_path_splitted[-2]

            if path_without_filename and path_without_filename[0] == "/":
                full_uri =  f"{url_parsed.scheme}://{url_parsed.netloc}{path_without_filename}"
            else:
                path = url_parsed.path.split('/')
                path.pop()
                path = "/".join(path)
                full_uri =  f"{url_parsed.scheme}://{url_parsed.netloc}{path}/{path_without_filename}"
            #_LOGGER.debug("URI: %s" % (full_uri + "/" + filename_with_ext))

            content += "/proxy/" + username + "/" + password + "/" + base64.b64encode(full_uri.encode("utf-8")).decode("utf-8")  + "/" + filename_with_ext + "\n"

        if ext_x_media_sequence < self.m_ext_x_media_sequence:
            _LOGGER.error(f"EXT-X-MEDIA-SEQUENCE rollbacks detected ! (Server seq: {ext_x_media_sequence}, Client seq: {self.m_ext_x_media_sequence}), continue anyway ...")

        self.m_ext_x_media_sequence = ext_x_media_sequence
        return content.encode("utf-8")
