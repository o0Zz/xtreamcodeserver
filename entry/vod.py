import datetime
import time
import logging
from xtreamcodeserver.entry import *
from xtreamcodeserver.entry.entry import XTreamCodeEntry, XTreamCodeType
from xtreamcodeserver.interfaces.stream import IXTreamCodeStream

_LOGGER = logging.getLogger(__name__)

class XTreamCodeVod (XTreamCodeEntry):
    def __init__(self, name: str, extension: str, stream: IXTreamCodeStream, vod_id: int=None, cover_url: str=None, description: str=None):
        XTreamCodeEntry.__init__(self, name, XTreamCodeType.VOD, vod_id)
        self.m_stream = stream
        self.m_cover_url = cover_url
        self.m_backdrop_url = None
        self.m_description = description
        self.m_categories_ids = []
        self.m_added_timestamp = 0
        self.m_rate = 0
        self.m_container_extension = extension
        self.m_duration_s = 0
        self.m_release_date = datetime.datetime(year=1970, month=1, day=1)
        self.m_director = ""
        self.m_actors = []
        self.m_genres = []

        if self.m_container_extension and self.m_container_extension.startswith('.'):
            self.m_container_extension = self.m_container_extension[1:]
        
        assert(len(self.m_container_extension) <= 4)

    def set_backdrop_url(self, backdrop_url: str) -> None:
        self.m_backdrop_url = backdrop_url

    def set_rate(self, rate: float) -> None:
        self.m_rate = rate

    def set_release_date(self, release_date: datetime.datetime) -> None:
        if release_date is not None:
            self.m_release_date = release_date

    def set_duration_seconds(self, duration_s: int) -> None:
        self.m_duration_s = duration_s

    def set_director(self, director: str) -> None:
        self.m_director = director

    def set_actors(self, actors: list[str]) -> None:
        self.m_actors = actors

    def set_genres(self, genres: list[str]) -> None:
        self.m_genres = genres

    def set_added_timestamp(self, added_timestamp: int) -> None:
        self.m_added_timestamp = added_timestamp

    def add_category_id(self, category_id: int) -> None:
        self.m_categories_ids.append(category_id)

    def get_container_extension(self) -> str:
        return self.m_container_extension

    def get_category_id(self) -> int:
        return self.m_categories_ids[0]

    def get_stream(self) -> IXTreamCodeStream:
        return self.m_stream

    def get_cover_url(self) -> str:
        return self.m_cover_url

    def get_streams_json(self, num: int=0) -> dict:
        return {
            "num": num,  # Can be removed ?
            "name": self.m_name,
            "stream_type": "movie",
            "stream_id": self.m_id,
            "stream_icon": self.m_cover_url,  # self.m_icon.replace('/', '\\/') if self.m_icon is not None else None,
            "added": str(self.m_added_timestamp),
            "is_adult": "0",
            "category_id": str(self.m_categories_ids[0]),
            "category_ids": self.m_categories_ids,  # [str(x) for x in self.m_categories_ids]
            "custom_sid": None,
            "direct_source": "",
            "rating_5based": str(int(self.m_rate / 2)),
            "rating": self.m_rate,
            "container_extension": self.m_container_extension
        }

    def get_info_json(self):
        ret = {
            "info": {
                "tmdb_id": 0,
                "name": self.m_name,
                "o_name": self.m_name,
                "cover_big": self.m_cover_url,
                "movie_image": self.m_cover_url,
                "releasedate": f"{self.m_release_date.year}-{self.m_release_date.month}-{self.m_release_date.day}",
                "youtube_trailer": None,
                "director": self.m_director,
                "actors": ", ".join(self.m_actors),
                "cast": ", ".join(self.m_actors),
                "description": self.m_description,
                "plot": self.m_description,
                "age": "",
                "country": "",
                "genre": ", ".join(self.m_genres),
                "backdrop_path": [self.m_backdrop_url],
                "duration_secs": str(self.m_duration_s),
                "duration": time.strftime("%H:%M:%S", time.gmtime(self.m_duration_s)),
                "video": {},
                "audio": {},
                "bitrate": 0,
                "rating": str(self.m_rate),
            },
            "movie_data": {
                "stream_id": str(self.get_entry_id()),
                "name": self.m_name,
                "added": str(self.m_added_timestamp),
                "category_id": str(self.m_categories_ids[0]),
                "category_ids": self.m_categories_ids,
                "container_extension": self.m_container_extension,
                "custom_sid": None,
                "direct_source": ""
            }
        }

        return ret


