from abc import abstractmethod
import datetime

class IXTreamCodeDateTimeProvider:

    @abstractmethod
    def utcnow(self) -> datetime.datetime:
        raise NotImplementedError("Must be implemented by Subclasses !")
