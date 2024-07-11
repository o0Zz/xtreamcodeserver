import logging

from xtreamcodeserver.epg.epgprogram import XTreamCodeEPGProgram

_LOGGER = logging.getLogger(__name__)

class XTreamCodeEPGChannel:
    def __init__(self, channel_id: str, display_name: str="", icon :str=""):
        assert channel_id is not None and len(channel_id) > 0
        self.m_channel_id = channel_id
        self.m_display_name = display_name
        self.m_cover_url = icon
        self.m_programme_list = []
        
    def add_programme(self, programme: XTreamCodeEPGProgram):
        self.m_programme_list.append(programme)

        #Sort the list by start time
        self.m_programme_list.sort(key=lambda d: d.get_datetime_start_utc())

    def get_channel_id(self) -> str:
        return self.m_channel_id

    def get_display_name(self) -> str:
        return self.m_display_name

    def get_cover_url(self) -> str:
        return self.m_cover_url

    def get_programme_list(self) -> list[XTreamCodeEPGProgram]:
        return self.m_programme_list