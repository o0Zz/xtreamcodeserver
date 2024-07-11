import datetime
import logging
from xtreamcodeserver.entry.container import XTreamCodeContainer
from xtreamcodeserver.entry.entry import XTreamCodeType
from xtreamcodeserver.entry.serie_episode import XTreamCodeEpisode
from xtreamcodeserver.entry.serie_season import XTreamCodeSeason

_LOGGER = logging.getLogger(__name__)

class XTreamCodeSerie(XTreamCodeContainer):
    def __init__(self, name: str, serie_id: int=None, cover_url: str=None, description: str=None):
        XTreamCodeContainer.__init__(self, name, XTreamCodeType.SERIE, serie_id, 0)
        self.m_cover_url = cover_url
        self.m_description = description
        self.m_categories_ids = []
        self.m_lastmodified_timestamp = 0
        self.m_rate = 0.0
        self.m_release_date = datetime.datetime(year=1970, month=1, day=1)
        self.m_director = ""
        self.m_actors = []
        self.m_genres = []

    def add_season(self, season: XTreamCodeSeason) -> None:
        self[season] = season

    def set_rate(self, rate: float) -> None:
        self.m_rate = rate

    def set_release_date(self, release_date: datetime.datetime) -> None:
        if release_date is not None:
            self.m_release_date = release_date

    def set_director(self, director: str) -> None:
        self.m_director = director

    def set_actors(self, actors: list[str]) -> None:
        self.m_actors = actors

    def set_genres(self, genres: list[str]) -> None:
        self.m_genres = genres

    def set_lastmodified_timestamp(self, lastmodified_timestamp: int) -> None:
        self.m_lastmodified_timestamp = lastmodified_timestamp

    def add_category_id(self, category_id: int) -> None:
        self.m_categories_ids.append(category_id)

    def get_category_id(self) -> int:
        return self.m_categories_ids[0]

    def get_cover_url(self) -> str:
        return self.m_cover_url

    def get_season(self, season_number: int):
        for season in self.get_all_seasons():
            if season.get_season_number() == season_number:
                return season
        return None
    
    def get_all_seasons(self) -> list[XTreamCodeSeason]:
        return self.get_entries()
    
    def get_all_episodes(self) -> list[XTreamCodeEpisode]:
        episodes = []
        for season in self.get_all_seasons():
            episodes.extend(season.get_all_episodes())
        return episodes

    def get_serie_json(self, num: int=None) -> dict:

        ret = {
            "name": self.m_name,
            "series_id": self.get_entry_id(),
            "cover": self.m_cover_url,
            "plot": self.m_description,
            "cast": ", ".join(self.m_actors),
            "director": self.m_director,
            "genre": ", ".join(self.m_genres),
            "releaseDate": f"{self.m_release_date.year}-{self.m_release_date.month}-{self.m_release_date.day}",
            "last_modified": str(self.m_lastmodified_timestamp),
            "rating": str(self.m_rate),
            "rating_5based": str(int(self.m_rate / 2)),
            "backdrop_path": [],
            "youtube_trailer": None,
            "tmdb": "0",
            "episode_run_time": "60",
            "category_id": str(self.m_categories_ids[0]),
            "category_ids": self.m_categories_ids
        }

        if num is not None:
            ret["num"] = num

        return ret

    def get_serie_info_json(self):
        ret = {
            "seasons": [], 
            "info": self.get_serie_json(), 
            "episodes": {}
        }

        for season in self.get_all_seasons():
            ret["seasons"].append( season.get_info_json() )  
            ret["episodes"][str(season.get_season_number())] = season.get_episodes_json()

        return ret

