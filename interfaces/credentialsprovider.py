from abc import abstractmethod

from xtreamcodeserver.credentials.credentials import XTreamCodeCredentials

class IXTreamCodeCredentialsProvider:
    
    @abstractmethod
    def get_credentials(self, username: str, password: str) -> XTreamCodeCredentials:
        raise NotImplementedError("Must be implemented by Subclasses !")
  