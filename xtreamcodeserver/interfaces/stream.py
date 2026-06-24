from abc import abstractmethod
from http import HTTPStatus

class IXTreamCodeStream:

    @abstractmethod
    def clone(self) -> "IXTreamCodeStream":
        # Return a fresh, independent stream built from the same configuration.
        # The server keeps a single stream instance per entry but is multi-threaded,
        # so every request must operate on its own instance to avoid sharing
        # per-request state (file descriptors, offsets, ffmpeg processes, ...)
        # across concurrent connections.
        raise NotImplementedError("Must be implemented by Subclasses !")

    @abstractmethod
    def get_uri(self) -> str:
        raise NotImplementedError("Must be implemented by Subclasses !")

    @abstractmethod
    def set_uri(self, uri: str) -> None:
        raise NotImplementedError("Must be implemented by Subclasses !")

    @abstractmethod
    def is_available(self) -> bool:
        raise NotImplementedError("Must be implemented by Subclasses !")

    @abstractmethod
    def is_opened(self) -> bool:
        raise NotImplementedError("Must be implemented by Subclasses !")

    @abstractmethod
    def is_end_of_stream(self) -> bool:
        raise NotImplementedError("Must be implemented by Subclasses !")

    @abstractmethod
    def open(self, http_req_path: str, http_req_headers: dict) -> bool:
        raise NotImplementedError("Must be implemented by Subclasses !")
        
    @abstractmethod
    def close(self) -> None:
        raise NotImplementedError("Must be implemented by Subclasses !")

    @abstractmethod
    def read_chunk(self, chunk_size: int) -> bytes:
        raise NotImplementedError("Must be implemented by Subclasses !")

    @abstractmethod
    def get_http_headers(self) -> dict:
        raise NotImplementedError("Must be implemented by Subclasses !")
    
    @abstractmethod
    def get_http_status_code(self) -> HTTPStatus:
        raise NotImplementedError("Must be implemented by Subclasses !")
