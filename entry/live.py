import logging
from xtreamcodeserver.entry import *
from xtreamcodeserver.entry.entry import XTreamCodeEntry, XTreamCodeType
from xtreamcodeserver.interfaces.stream import IXTreamCodeStream

_LOGGER = logging.getLogger(__name__)

class XTreamCodeLive(XTreamCodeEntry):
    def __init__(self, name: str, stream: IXTreamCodeStream, epg_channel_id: str=None, live_id: int=None, icon_url: str=None):
        XTreamCodeEntry.__init__(self, name, XTreamCodeType.LIVE, live_id)
        self.m_stream = stream
        self.m_cover_url = icon_url
        self.m_categories_ids = []
        self.m_added_timestamp = 0
        self.m_epg_channel_id = epg_channel_id

    def add_category_id(self, category_id: int) -> None:
        self.m_categories_ids.append(category_id)

    def get_category_id(self) -> int:
        return self.m_categories_ids[0]

    def get_stream(self) -> IXTreamCodeStream:
        return self.m_stream

    def get_cover_url(self) -> str:
        return self.m_cover_url

    def get_epg_channel_id(self) -> str:
        return self.m_epg_channel_id

    def get_streams_json(self, num: int=0) -> dict:
        return {
            "num": num,
            "name": self.m_name,
            "stream_type": "live",
            "stream_id": self.m_id,
            "stream_icon": self.m_cover_url,  # self.m_cover_url.replace('/', '\\/') if self.m_cover_url is not None else None,
            "added": str(self.m_added_timestamp),
            "is_adult": "0",
            "category_id": str(self.m_categories_ids[0]),
            "category_ids": self.m_categories_ids,  # [str(x) for x in self.m_categories_ids]
            "custom_sid": None,
            "direct_source": "",
            "epg_channel_id": self.m_epg_channel_id,
            "tv_archive": 0,
            "tv_archive_duration": 0
        }
       
        return ret

