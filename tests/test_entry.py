import datetime
import requests
from xtreamcodeserver.entry.serie import XTreamCodeSerie
from xtreamcodeserver.entry.serie_episode import XTreamCodeEpisode
from xtreamcodeserver.entry.serie_season import XTreamCodeSeason
from xtreamcodeserver.entry.vod import XTreamCodeVod
from xtreamcodeserver.entry.category import XTreamCodeCategory
from xtreamcodeserver.entry.entry import XTreamCodeEntry, XTreamCodeType
from xtreamcodeserver.entry.live import XTreamCodeLive
from xtreamcodeserver.providers.inmemory.entry_provider import XTreamCodeEntryMemoryProvider
from xtreamcodeserver.server import XTreamCodeServer
from xtreamcodeserver.stream.memorystream import XTreamCodeMemoryStream

class TestEntry:
    
    def setup_class(self):
        self.bind_port = 8082
        self.entry_provider = XTreamCodeEntryMemoryProvider()
        self.server = XTreamCodeServer(self.entry_provider, None, None)
        self.server.setup(bind_port=self.bind_port)
        self.server.start()
        self.test_url = f"http://127.0.0.1:{self.bind_port}/"

        category = XTreamCodeCategory(name="test", category_type=XTreamCodeType.LIVE, category_id=1)
        category.add_entry(XTreamCodeLive(name="live_test", stream=XTreamCodeMemoryStream(b'live', "video/mpg"), epg_channel_id='tf1.fr', live_id=2))
        self.entry_provider.add_category(category)

        category = XTreamCodeCategory(name="test", category_type=XTreamCodeType.VOD, category_id=3)
        category.add_entry(XTreamCodeVod(name="test", extension="mkv", stream=XTreamCodeMemoryStream(b'movie_stream', "video/x-matroska"), vod_id=4, cover_url="http://cover.com", description="This is the description for test"))
        self.entry_provider.add_category(category)
        
        category = XTreamCodeCategory(name="serie_categorie", category_type=XTreamCodeType.SERIE, category_id=5)
        serie = XTreamCodeSerie(name="serie_title", serie_id=6)
        season = XTreamCodeSeason(season_number=1, name="serie_season", season_id=7, cover_url="http://cover.com", description="This is the description for serie_season")
        episode = XTreamCodeEpisode(episode_number=1, name="serie_episode", extension="mkv", stream=XTreamCodeMemoryStream(b'serie_stream', "video/x-matroska"), episode_id=8)

        episode.set_rate(1.0)
        episode.set_release_date(datetime.datetime(year=2024, month=1, day=1))
        episode.set_duration_seconds(60)
        episode.set_director("director")
        episode.set_actors(["actor1", "actor2"])
        episode.set_genres(["genre1", "genre2"])
        episode.set_added_timestamp(1704067200)

        season.add_episode(episode)
        serie.add_season(season)
        category.add_entry(serie)
        self.entry_provider.add_category(category)

    def teardown_class(self):
        self.server.stop()

    def test_live_category(self):
        r = requests.get(self.test_url + "player_api.php?username=test&password=test&action=get_live_categories")
        assert r.json() == [{'category_id': '1', 'category_name': 'test', 'parent_id': 0}]

    def test_live_get_all_streams(self):
        r = requests.get(self.test_url + "player_api.php?username=test&password=test&action=get_live_streams&category_id=*&")
        assert r.json() == [
            {
                'num': 1,
                'name': 'live_test',
                'stream_type': 'live',
                'stream_id': 2,
                'stream_icon': None,
                'added': '0',
                'is_adult': '0',
                'category_id': '1',
                'category_ids': [1],
                'custom_sid': None,
                'direct_source': '',
                'epg_channel_id': 'tf1.fr',
                'tv_archive': 0,
                'tv_archive_duration': 0
            }]
    
    def test_live_streaming(self):
        r = requests.get(self.test_url + "live/test/test/2.ts")
        assert r.content == b'live'

    def test_vod_category(self):
        r = requests.get(self.test_url + "player_api.php?username=test&password=test&action=get_vod_categories")
        assert r.json() == [{'category_id': '3', 'category_name': 'test', 'parent_id': 0}]

    def test_vod_get_all_streams(self):
        r = requests.get(self.test_url + "player_api.php?username=test&password=test&action=get_vod_streams&category_id=*&")
        assert r.json() == [{
                    'num': 1,
                    'name': 'test',
                    'stream_type': 'movie',
                    'stream_id': 4,
                    'stream_icon': 'http://cover.com',
                    'added': '0',
                    'is_adult': '0',
                    'category_id': '3',
                    'category_ids': [3],
                    'custom_sid': None,
                    'direct_source': '',
                    'rating_5based': '0',
                    'rating': 0,
                    'container_extension': 'mkv'
                }
            ]

    def test_vod_streaming(self):
        r = requests.get(self.test_url + "movies/test/test/4.mkv")
        assert r.content == b'movie_stream'

    def test_series_category(self):
        r = requests.get(self.test_url + "player_api.php?username=test&password=test&action=get_series_categories")
        assert r.json() == [{'category_id': '5', 'category_name': 'serie_categorie', 'parent_id': 0}]

    def test_series_list(self):
        r = requests.get(self.test_url + "player_api.php?username=test&password=test&action=get_series")
        assert r.json() == [{'name': 'serie_title', 'series_id': 6, 'cover': None, 'plot': None, 'cast': '', 'director': '', 'genre': '', 'releaseDate': '1970-1-1', 'last_modified': '0', 'rating': '0.0', 'rating_5based': '0', 'backdrop_path': [], 'youtube_trailer': None, 'tmdb': '0', 'episode_run_time': '60', 'category_id': '5', 'category_ids': [5], 'num': 1}]

    def test_series_streaming(self):
        r = requests.get(self.test_url + "/series/test/test/8.mkv")
        assert r.content == b'serie_stream'

    def test_m3u(self):
        r = requests.get(self.test_url + "/get.php?username=test&password=test&type=m3u_plus&output=ts")

        assert r.text  == f"""#EXTM3U
#EXTINF:-1 tvg-ID="tf1.fr" tvg-name="live_test" tvg-logo="" group-title="test",live_test
http://127.0.0.1:{self.bind_port}/test/test/2.ts
#EXTINF:-1 tvg-ID="" tvg-name="test" tvg-logo="http://cover.com" group-title="test",test
http://127.0.0.1:{self.bind_port}/test/test/4.mkv
#EXTINF:-1 tvg-ID="" tvg-name="serie_episode" tvg-logo="" group-title="serie_categorie",serie_episode
http://127.0.0.1:{self.bind_port}/test/test/8.mkv"""