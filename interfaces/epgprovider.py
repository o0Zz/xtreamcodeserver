from abc import abstractmethod

from xtreamcodeserver.epg.epgchannel import XTreamCodeEPGChannel

class IXTreamCodeEPGProvider:

    @abstractmethod
    def get_channel(self, channel_id: str) -> XTreamCodeEPGChannel:
        raise NotImplementedError("Must be implemented by Subclasses !")

    @abstractmethod
    def get_channels(self) -> list[XTreamCodeEPGChannel]:
        raise NotImplementedError("Must be implemented by Subclasses !")