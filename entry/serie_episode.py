import datetime
import time
import logging
from xtreamcodeserver.entry.entry import XTreamCodeType, XTreamCodeEntry
from xtreamcodeserver.interfaces.stream import IXTreamCodeStream

_LOGGER = logging.getLogger(__name__)

class XTreamCodeEpisode(XTreamCodeEntry):
    def __init__(self, episode_number: int, name: str, extension: str,  stream: IXTreamCodeStream, episode_id: int=None, cover_url: str=None, description: str=None):
        XTreamCodeEntry.__init__(self, name, XTreamCodeType.EPISODE, episode_id, episode_number)
        self.m_season_number = None
        self.m_episode_number = episode_number
        self.m_stream = stream
        self.m_cover_url = cover_url
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

    def set_season(self, season_number: int) -> None:
        self.m_season_number = season_number

    def set_rate(self, rate: float):
        self.m_rate = rate

    def set_release_date(self, release_date: datetime.datetime):
        if release_date is not None:
            self.m_release_date = release_date

    def set_duration_seconds(self, duration_s: int):
        self.m_duration_s = duration_s

    def set_director(self, director: str):
        self.m_director = director

    def set_actors(self, actors: list[str]):
        self.m_actors = actors

    def set_genres(self, genres: list[str]):
        self.m_genres = genres

    def set_added_timestamp(self, added_timestamp: int):
        self.m_added_timestamp = added_timestamp

    def add_category_id(self, category_id: int):
        self.m_categories_ids.append(category_id)

    def get_container_extension(self) -> str:
        return self.m_container_extension

    def get_category_id(self) -> int:
        return self.m_categories_ids[0]

    def get_stream(self) -> IXTreamCodeStream:
        return self.m_stream

    def get_cover_url(self) -> str:
        return self.m_cover_url

    def get_info_json(self) -> dict:
        ret = {
                "id": str(self.get_entry_id()),
                "episode_num": self.m_episode_number,
                "title": self.m_name,
                "container_extension": self.m_container_extension,
                "info": {
					"duration_secs": self.m_duration_s,
                    "duration": time.strftime("%H:%M:%S", time.gmtime(self.m_duration_s)),
                    "video": {},
					"audio": {},
                    "bitrate": 0,
                    "movie_image": self.m_cover_url
				},
                "custom_sid": None,
                "added": str(self.m_added_timestamp),
                "season": self.m_season_number,
                "direct_source": ""
            }
        

        return ret


