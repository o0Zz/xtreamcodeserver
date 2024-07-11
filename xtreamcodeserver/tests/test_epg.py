
import datetime
import requests
from xtreamcodeserver.entry.category import XTreamCodeCategory
from xtreamcodeserver.entry.entry import XTreamCodeType
from xtreamcodeserver.entry.live import XTreamCodeLive
from xtreamcodeserver.epg.epgchannel import XTreamCodeEPGChannel
from xtreamcodeserver.epg.epgprogram import XTreamCodeEPGProgram
from xtreamcodeserver.interfaces.datetimeprovider import IXTreamCodeDateTimeProvider
from xtreamcodeserver.providers.inmemory.entry_provider import XTreamCodeEntryMemoryProvider
from xtreamcodeserver.providers.inmemory.epg_provider import XTreamCodeEPGMemoryProvider
from xtreamcodeserver.server import XTreamCodeServer
from xtreamcodeserver.stream.memorystream import XTreamCodeMemoryStream

class DateTimeProviderTest(IXTreamCodeDateTimeProvider):
    def __init__(self) -> None:
        self.dt = datetime.datetime(year=2024, month=1, day=1, hour=0, minute=30, tzinfo=datetime.timezone.utc)

    def utcnow(self) -> datetime.datetime:
        return self.dt

class TestEPG:
    
    def setup_class(self):
        self.bind_port = 8083
        self.epg_provider = XTreamCodeEPGMemoryProvider()
        self.entry_provider = XTreamCodeEntryMemoryProvider()
        self.datetime_provider = DateTimeProviderTest()
        self.server = XTreamCodeServer(self.entry_provider, self.epg_provider, None, self.datetime_provider)
        self.server.setup(bind_port=self.bind_port)
        self.server.start()
        self.test_url = f"http://127.0.0.1:{self.bind_port}"

        category = XTreamCodeCategory("test", XTreamCodeType.LIVE, 1)
        category.add_entry(XTreamCodeLive("live_test", None, 'tf1.fr', 2))
        self.entry_provider.add_category(category)
        
        epg_channel = XTreamCodeEPGChannel("tf1.fr", "displayname", "iconurl")
        epg_channel.add_programme(XTreamCodeEPGProgram(datetime.datetime(year=2024, month=1, day=1, hour=2), datetime.datetime(year=2024, month=1, day=1, hour=3), "title2", "desc"))
        epg_channel.add_programme(XTreamCodeEPGProgram(datetime.datetime(year=2024, month=1, day=1, hour=3), datetime.datetime(year=2024, month=1, day=1, hour=4), "title3", "desc"))
        epg_channel.add_programme(XTreamCodeEPGProgram(datetime.datetime(year=2024, month=1, day=1, hour=1), datetime.datetime(year=2024, month=1, day=1, hour=2), "title1", "desc"))

        self.epg_provider.add_channel(epg_channel)

    def teardown_class(self):
        self.server.stop()

    def test_epg_limit(self):
        self.datetime_provider.dt = datetime.datetime(year=2024, month=1, day=1, tzinfo=datetime.timezone.utc)
        r = requests.get(self.test_url + "/player_api.php?username=test&password=test&action=get_short_epg&stream_id=2&limit=2")
        assert r.json() == { 
            'epg_listings': 
            [
                {'id': '0', 'epg_id': '0', 'title': 'dGl0bGUx', 'lang': '', 'start': '2024-01-01 00:00:00', 'end': '2024-01-01 01:00:00', 'description': 'ZGVzYw==', 'channel_id': 'tf1.fr', 'start_timestamp': '1704067200', 'stop_timestamp': '1704070800', 'stream_id': '2'},
                {'id': '0', 'epg_id': '0', 'title': 'dGl0bGUy', 'lang': '', 'start': '2024-01-01 01:00:00', 'end': '2024-01-01 02:00:00', 'description': 'ZGVzYw==', 'channel_id': 'tf1.fr', 'start_timestamp': '1704070800', 'stop_timestamp': '1704074400', 'stream_id': '2'}
            ]
        }

    def test_epg_simple_data_table(self):
        self.datetime_provider.dt = datetime.datetime(year=2024, month=1, day=1, tzinfo=datetime.timezone.utc)
        r = requests.get(self.test_url + "/player_api.php?username=test&password=test&action=get_simple_data_table&stream_id=2")
        assert r.json() == { 
            'epg_listings': 
            [
                {'id': '0', 'epg_id': '0', 'title': 'dGl0bGUx', 'lang': '', 'start': '2024-01-01 00:00:00', 'end': '2024-01-01 01:00:00', 'description': 'ZGVzYw==', 'channel_id': 'tf1.fr', 'start_timestamp': '1704067200', 'stop_timestamp': '1704070800', 'now_playing': 1, 'has_archive': 0},
                {'id': '0', 'epg_id': '0', 'title': 'dGl0bGUy', 'lang': '', 'start': '2024-01-01 01:00:00', 'end': '2024-01-01 02:00:00', 'description': 'ZGVzYw==', 'channel_id': 'tf1.fr', 'start_timestamp': '1704070800', 'stop_timestamp': '1704074400', 'now_playing': 0, 'has_archive': 0},
                {'id': '0', 'epg_id': '0', 'title': 'dGl0bGUz', 'lang': '', 'start': '2024-01-01 02:00:00', 'end': '2024-01-01 03:00:00', 'description': 'ZGVzYw==', 'channel_id': 'tf1.fr', 'start_timestamp': '1704074400', 'stop_timestamp': '1704078000', 'now_playing': 0, 'has_archive': 0}
            ]
        }

    def test_epg_out_of_range(self):
        self.datetime_provider.dt = datetime.datetime(year=2024, month=1, day=2, tzinfo=datetime.timezone.utc)
        r = requests.get(self.test_url + "/player_api.php?username=test&password=test&action=get_short_epg&stream_id=2")
        assert r.json() == {'epg_listings': []}

    def test_epg_stream_not_found(self):
        r = requests.get(self.test_url + "/player_api.php?username=test&password=test&action=get_short_epg&stream_id=404")
        assert r.json() == {'epg_listings': []}

    def test_epg_download_all_xmltv(self):
        self.datetime_provider.dt = datetime.datetime(year=2024, month=1, day=1, tzinfo=datetime.timezone.utc)
        r = requests.get(self.test_url + "/xmltv.php?username=test&password=test")
        assert r.text == f"""<?xml version="1.0" encoding="utf-8" ?>
<!DOCTYPE tv SYSTEM "xmltv.dtd">
<tv generator-info-name="pyXTreamCodeServer" generator-info-url="http://127.0.0.1:{self.bind_port}">
<channel id="tf1.fr"><display-name>displayname</display-name><icon src="iconurl"/></channel>
<programme start="20240101000000" stop="20240101010000" channel="tf1.fr"><title>title1</title><desc>desc</desc></programme>
<programme start="20240101010000" stop="20240101020000" channel="tf1.fr"><title>title2</title><desc>desc</desc></programme>
<programme start="20240101020000" stop="20240101030000" channel="tf1.fr"><title>title3</title><desc>desc</desc></programme>
</tv>"""