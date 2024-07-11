from abc import abstractmethod
from http import HTTPStatus
from xtreamcodeserver.entry.entry import XTreamCodeType

class IXTreamCodeStream:
    
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
