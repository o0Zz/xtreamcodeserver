
import logging
import threading
from xtreamcodeserver.epg.epgchannel import XTreamCodeEPGChannel

from xtreamcodeserver.interfaces.epgprovider import IXTreamCodeEPGProvider

_LOGGER = logging.getLogger(__name__)

class XTreamCodeEPGMemoryProvider (IXTreamCodeEPGProvider):
    def __init__(self):
        self.m_lock = threading.RLock()  # Used to avoid concurrent access to members
        self.m_epg_channels = {}  # Lock needed

    # ------------------------------------------------------------

    def add_channel(self, epg_channel: XTreamCodeEPGChannel):
        with self.m_lock:
            self.m_epg_channels[epg_channel.get_channel_id()] = epg_channel

    # ------------------------------------------------------------
        
    def get_channel(self, channel_id: str) -> XTreamCodeEPGChannel:
        with self.m_lock:
            return self.m_epg_channels.get(channel_id)

    # ------------------------------------------------------------

    def get_channels(self) -> list[XTreamCodeEPGChannel]:
        with self.m_lock:
            return self.m_epg_channels.copy().items()