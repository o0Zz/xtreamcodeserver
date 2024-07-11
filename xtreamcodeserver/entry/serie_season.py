import datetime
import logging
from xtreamcodeserver.entry.container import XTreamCodeContainer
from xtreamcodeserver.entry.entry import XTreamCodeType
from xtreamcodeserver.entry.serie_episode import XTreamCodeEpisode

_LOGGER = logging.getLogger(__name__)

class XTreamCodeSeason(XTreamCodeContainer):
    def __init__(self, season_number: int, name: str, season_id: int = None, cover_url:str = None, description:str=None):
        XTreamCodeContainer.__init__(self, name, XTreamCodeType.SEASON, season_id, season_number)
        self.m_season_number = season_number
        self.m_cover_url = cover_url
        self.m_description = description
        self.m_release_date = datetime.datetime(year=1970, month=1, day=1)

    def add_episode(self, serie_episode: XTreamCodeEpisode):
        self[serie_episode] = serie_episode
        serie_episode.set_season(self.m_season_number)

    def set_release_date(self, release_date: datetime.datetime):
        if release_date is not None:
            self.m_release_date = release_date

    def get_cover_url(self) -> str:
        return self.m_cover_url

    def get_season_number(self) -> int:
        return self.m_season_number
    
    def get_all_episodes(self) -> list[XTreamCodeEpisode]:
        return self.get_entries()
    
    def get_info_json(self) -> dict:
        ret = {
            "air_date": f"{self.m_release_date.year}-{self.m_release_date.month}-{self.m_release_date.day}",
            "episode_count": len(self.get_all_episodes()),
            "id": self.m_id,
            "name": self.m_name,
            "overview": self.m_description,
            "season_number": self.m_season_number - 1, # 0 based
            "cover": self.m_cover_url,
            "cover_big": self.m_cover_url
        }

        return ret


    def get_episodes_json(self):
        ret = []
        for episode in self.get_all_episodes():
            ret.append(episode.get_info_json())

        return ret