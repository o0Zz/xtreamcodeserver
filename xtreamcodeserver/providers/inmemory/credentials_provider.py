
import hmac
import logging
import threading

from xtreamcodeserver.credentials.credentials import XTreamCodeCredentials
from xtreamcodeserver.interfaces.credentialsprovider import IXTreamCodeCredentialsProvider

_LOGGER = logging.getLogger(__name__)

class XTreamCodeCredentialsMemoryProvider (IXTreamCodeCredentialsProvider):
    def __init__(self):
        self.m_lock = threading.Lock()
        self.m_credentials_list = {}
    
    def add_or_update_credentials(self, credentials: XTreamCodeCredentials) -> None:
        with self.m_lock:
            self.m_credentials_list[credentials.get_username()] = credentials

    def get_credentials(self, username: str, password: str) -> XTreamCodeCredentials:
        with self.m_lock:
            credential = self.m_credentials_list.get(username)
            if credential is not None and XTreamCodeCredentialsMemoryProvider.__password_matches(credential.get_password(), password):
                return credential
            
        return None

    @staticmethod
    def __password_matches(expected: str, provided: str) -> bool:
        if expected is None or provided is None:
            return expected is provided

        # Constant-time comparison: do not leak password length/prefix through timing.
        return hmac.compare_digest(str(expected).encode("utf-8"), str(provided).encode("utf-8"))
