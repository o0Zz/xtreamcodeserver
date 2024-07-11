import logging
import datetime

_LOGGER = logging.getLogger(__name__)

class XTreamCodeCredentials:
    def __init__(self, username: str, password: str, expiration_date: datetime.datetime = None, active: bool = True, max_connections: int = 1, desactive_on_expiration: bool = True):
        assert expiration_date is None or (expiration_date.tzinfo is not None and expiration_date.tzinfo.utcoffset(expiration_date) is not None)
        self.m_username = username
        self.m_password = password
        self.m_expiration_date = expiration_date
        self.m_active = active
        self.m_max_connections = max_connections
        self.m_desactive_on_expiration = desactive_on_expiration
                
    def get_username(self) -> str:
        return self.m_username

    def get_password(self) -> str:
        return self.m_password

    def set_expiration_date(self, expiration_date: datetime.datetime) -> None:
        assert expiration_date is None or (expiration_date.tzinfo is not None and expiration_date.tzinfo.utcoffset(expiration_date) is not None)
        self.m_expiration_date = expiration_date

    def get_expiration_date(self) -> datetime.datetime:
        return self.m_expiration_date

    def set_active(self, active: bool) -> None:
        self.m_active = active

    def is_active(self, utcnow: datetime.datetime) -> bool:
        if self.m_desactive_on_expiration:
            if (self.m_expiration_date is not None and self.m_expiration_date < utcnow):
                return False

        return self.m_active
    
    def set_max_connections(self, max_connections: int) -> None:
        self.m_max_connections = max_connections
        
    def get_max_connections(self) -> int:
        return self.m_max_connections
    
