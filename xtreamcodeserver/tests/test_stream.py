import re
import requests
from xtreamcodeserver.entry.live import XTreamCodeLive
from xtreamcodeserver.entry.vod import XTreamCodeVod
from xtreamcodeserver.entry.category import XTreamCodeCategory
from xtreamcodeserver.entry.entry import XTreamCodeType
from xtreamcodeserver.providers.inmemory.entry_provider import XTreamCodeEntryMemoryProvider
from xtreamcodeserver.server import XTreamCodeServer
from xtreamcodeserver.stream.filesystemstream import XTreamCodeFileSystemStream
from xtreamcodeserver.stream.httpredirectstream import XTreamCodeHTTPRedirectStream
from xtreamcodeserver.stream.httpstream import XTreamCodeHTTPStream
from xtreamcodeserver.stream.playlistproxystream import XTreamCodePlaylistProxyStream
from xtreamcodeserver.stream.memorystream import XTreamCodeMemoryStream

class TestStream:
    
    def setup_class(self):
        self.bind_port = 8085
        self.entry_provider = XTreamCodeEntryMemoryProvider()
        self.server = XTreamCodeServer(self.entry_provider, None, None)
        self.server.setup(bind_port=self.bind_port)
        self.server.start()
        self.test_url = f"http://127.0.0.1:{self.bind_port}"
        self.test_url_m3u8 = f"https://demo.unified-streaming.com/k8s/vod2live/stable/unified-learning.isml/unified-learning-audio_eng=128000-video=2200000.m3u8"
 
    def teardown_class(self):
        self.server.stop()

    def test_filesystem_stream(self):
        category = XTreamCodeCategory(name="test", category_type=XTreamCodeType.VOD, category_id=1)
        category.add_entry(XTreamCodeVod(name="test", extension="mkv", stream=XTreamCodeFileSystemStream(__file__), vod_id=2))
        self.entry_provider.set_categories({1: category})

        r = requests.get(self.test_url + "/movies/test/test/2.mkv")
        file_content = open(__file__, "rb").read()
        assert r.content == file_content
    
    def test_http_stream_correct_content(self):
        category = XTreamCodeCategory(name="test", category_type=XTreamCodeType.VOD, category_id=1)
        category.add_entry(XTreamCodeVod(name="test", extension="mkv", stream=XTreamCodeHTTPStream("https://httpbin.org/get"), vod_id=2))
        self.entry_provider.set_categories({1: category})

        r = requests.get(self.test_url + "/movies/test/test/2.mkv")
        assert r.json()["url"] == 'https://httpbin.org/get'

    def test_http_stream_retry_live(self):
        stream = XTreamCodeHTTPStream(self.test_url_m3u8)
        stream.open(None, {})
        stream.m_is_live = True #Fake live stream

        ret = stream.read_chunk(128)
        assert len(ret) > 0

        stream.close() #Force close to simulate remote disconnection
        ret = stream.read_chunk(128) #Should reconnect and read 1 more chunk
        assert len(ret) > 0
        stream.close()

    def test_http_stream_no_retry_not_live(self):
        stream = XTreamCodeHTTPStream(self.test_url_m3u8)
        stream.open(None, {})

        ret = stream.read_chunk(128)
        assert len(ret) > 0

        stream.close() #Force close to simulate remote disconnection
        ret = stream.read_chunk(128) #Should return None
        assert ret == None
        stream.close()

    def test_httpredirect_stream(self):
        category = XTreamCodeCategory(name="test", category_type=XTreamCodeType.VOD, category_id=1)
        category.add_entry(XTreamCodeVod(name="test", extension="mkv", stream=XTreamCodeHTTPRedirectStream(self.test_url_m3u8), vod_id=2))
        self.entry_provider.set_categories({1: category})

        r = requests.get(self.test_url + "/movies/test/test/2.mkv", allow_redirects=False)
        assert r.status_code == 302
        assert r.headers['Location'] == self.test_url_m3u8

    def test_playlist_proxy_stream_m3u8_parsing(self):
        category = XTreamCodeCategory(name="test", category_type=XTreamCodeType.LIVE, category_id=1)
        category.add_entry(XTreamCodeLive(name="test", stream=XTreamCodePlaylistProxyStream(XTreamCodeMemoryStream(
b"""
#EXTM3U
#EXT-X-VERSION:3
#EXT-X-MEDIA-SEQUENCE:1093
#EXT-X-ALLOW-CACHE:YES
#EXT-X-TARGETDURATION:12
#EXTINF:9.640000,
/path/to/file/1_1.ts
#EXTINF:11.520000,
/path/to/file/1_2.ts
#EXTINF:9.600000,
/path/to/file/1_3.ts
""", "application/x-mpegURL", "memory://test/file.m3u8")), live_id=2))
        self.entry_provider.set_categories({1: category})

        r = requests.get(self.test_url + "/live/test/test/2.m3u8")
        assert r.content == b"""#EXTM3U
#EXT-X-VERSION:3
#EXT-X-MEDIA-SEQUENCE:1093
#EXT-X-ALLOW-CACHE:YES
#EXT-X-TARGETDURATION:12
#EXTINF:9.640000,
/proxy/test/test/bWVtb3J5Oi8vdGVzdC9wYXRoL3RvL2ZpbGUvMV8x.ts
#EXTINF:11.520000,
/proxy/test/test/bWVtb3J5Oi8vdGVzdC9wYXRoL3RvL2ZpbGUvMV8y.ts
#EXTINF:9.600000,
/proxy/test/test/bWVtb3J5Oi8vdGVzdC9wYXRoL3RvL2ZpbGUvMV8z.ts
"""

    def test_playlist_proxy_stream_download(self):
        category = XTreamCodeCategory(name="test", category_type=XTreamCodeType.LIVE, category_id=1)
        category.add_entry(XTreamCodeLive(name="test", stream=XTreamCodePlaylistProxyStream(XTreamCodeHTTPStream(self.test_url_m3u8)), live_id=2))
        self.entry_provider.set_categories({1: category})

        r = requests.get(self.test_url + "/live/test/test/2.m3u8")
        assert r.text.startswith("#EXTM3U")

        url = "/proxy/" + re.search('/proxy/(.*)\n', r.text).group(1)
        r = requests.get(self.test_url + url)
        assert r.status_code//100 == 2
        assert len(r.content) > 0

    def test_memory_stream(self):
        category = XTreamCodeCategory(name="test", category_type=XTreamCodeType.VOD, category_id=1)
        category.add_entry(XTreamCodeVod(name="test", extension="mkv", stream=XTreamCodeMemoryStream(b'movie_stream', "video/x-matroska"), vod_id=2))
        self.entry_provider.set_categories({1: category})

        r = requests.get(self.test_url + "/movies/test/test/2.mkv")
        assert r.content == b'movie_stream'
