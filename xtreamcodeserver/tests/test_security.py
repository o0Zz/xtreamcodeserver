import base64
import threading
import time
import requests
from http import HTTPStatus
from xtreamcodeserver.credentials.credentials import XTreamCodeCredentials
from xtreamcodeserver.entry.category import XTreamCodeCategory
from xtreamcodeserver.entry.entry import XTreamCodeType
from xtreamcodeserver.entry.vod import XTreamCodeVod
from xtreamcodeserver.providers.inmemory.credentials_provider import XTreamCodeCredentialsMemoryProvider
from xtreamcodeserver.providers.inmemory.entry_provider import XTreamCodeEntryMemoryProvider
from xtreamcodeserver.server import XTreamCodeServer
from xtreamcodeserver.stream.memorystream import XTreamCodeMemoryStream
from xtreamcodeserver.providers.inmemory.proxy_registry import XTreamCodeProxyMemoryRegistry


class SlowMemoryStream(XTreamCodeMemoryStream):
    """Memory stream that blocks until released, to keep a stream slot busy."""
    gate = threading.Event()

    def clone(self):
        return SlowMemoryStream(self.m_data, self.m_mimetype, self.m_url)

    def read_chunk(self, chunk_size=8192):
        SlowMemoryStream.gate.wait(5)
        return super().read_chunk(chunk_size)


class TestSecurity:

    def setup_class(self):
        self.bind_port = 8087
        self.credentials = XTreamCodeCredentialsMemoryProvider()
        self.credentials.add_or_update_credentials(XTreamCodeCredentials("user1", "pass1", max_connections=1))
        self.credentials.add_or_update_credentials(XTreamCodeCredentials("user2", "pass2", max_connections=0))
        self.entry_provider = XTreamCodeEntryMemoryProvider()
        self.registry = XTreamCodeProxyMemoryRegistry(max_entries=2)
        self.server = XTreamCodeServer(self.entry_provider, None, self.credentials, self.registry)
        self.server.setup(bind_port=self.bind_port, max_auth_failures=3, auth_lockout_seconds=2)
        self.server.start()
        self.base_url = f"http://127.0.0.1:{self.bind_port}"

        category = XTreamCodeCategory(name="test", category_type=XTreamCodeType.VOD, category_id=1)
        category.add_entry(XTreamCodeVod(name="slow", extension="mkv", stream=SlowMemoryStream(b"0123456789", "video/x-matroska"), vod_id=2))
        category.add_entry(XTreamCodeVod(name="fast", extension="mkv", stream=XTreamCodeMemoryStream(b"movie_stream", "video/x-matroska"), vod_id=3))
        self.entry_provider.set_categories({1: category})

    def teardown_class(self):
        self.server.stop()

    # ---------------------------------------------------------------- /proxy/ SSRF

    def test_proxy_rejects_client_supplied_url(self):
        # The old scheme: base64(url) chosen by the client -> must not be accepted anymore
        for url in (f"{self.base_url}/user1/pass1", "http://127.0.0.1:1", "http://192.168.1.1"):
            b64 = base64.b64encode(url.encode()).decode()
            r = requests.get(f"{self.base_url}/proxy/user1/pass1/{b64}/segment.ts")
            assert r.status_code == HTTPStatus.NOT_FOUND
            b64url = base64.urlsafe_b64encode(url.encode()).decode()
            r = requests.get(f"{self.base_url}/proxy/user1/pass1/{b64url}/segment.ts")
            assert r.status_code == HTTPStatus.NOT_FOUND

    def test_proxy_rejects_unknown_token(self):
        r = requests.get(f"{self.base_url}/proxy/user1/pass1/doesnotexist/segment.ts")
        assert r.status_code == HTTPStatus.NOT_FOUND

    def test_proxy_rejects_unsafe_filename(self):
        token = self.registry.register(f"{self.base_url}/user1/pass1")
        r = requests.get(f"{self.base_url}/proxy/user1/pass1/{token}/..")
        assert r.status_code == HTTPStatus.NOT_FOUND

    def test_proxy_accepts_registered_token(self):
        token = self.registry.register(f"{self.base_url}/user1/pass1")
        r = requests.get(f"{self.base_url}/proxy/user1/pass1/{token}/xmltv.php")
        assert r.status_code == HTTPStatus.OK
        assert r.text.startswith("<?xml")

    def test_proxy_registry_is_bounded_and_opaque(self):
        registry = XTreamCodeProxyMemoryRegistry(max_entries=2)
        t1 = registry.register("http://upstream/live/u/p")
        assert registry.register("http://upstream/live/u/p") == t1
        assert "upstream" not in t1 and "u/p" not in t1
        registry.register("http://upstream/2")
        registry.register("http://upstream/3")
        assert registry.resolve(t1) is None  # Evicted (LRU)
        assert registry.resolve("http://upstream/3") is None  # A URL is not a token

    # ---------------------------------------------------------------- brute force

    def test_bruteforce_lockout(self):
        for _ in range(3):
            r = requests.get(f"{self.base_url}/player_api.php?username=user1&password=wrong")
            assert r.status_code == HTTPStatus.UNAUTHORIZED

        # Locked out: even the right password is refused during the lockout window
        r = requests.get(f"{self.base_url}/player_api.php?username=user1&password=pass1")
        assert r.status_code == HTTPStatus.TOO_MANY_REQUESTS

        time.sleep(2.2)
        r = requests.get(f"{self.base_url}/player_api.php?username=user1&password=pass1")
        assert r.status_code == HTTPStatus.OK

    # ---------------------------------------------------------------- max_connections

    def test_max_connections_enforced(self):
        SlowMemoryStream.gate.clear()
        results = {}

        def first_stream():
            results["first"] = requests.get(f"{self.base_url}/movies/user1/pass1/2.mkv")

        t = threading.Thread(target=first_stream)
        t.start()

        for _ in range(50):  # Wait until the first stream holds its slot
            if self.server.get_active_stream_count("user1") == 1:
                break
            time.sleep(0.05)
        assert self.server.get_active_stream_count("user1") == 1

        # Second concurrent stream for the same account -> refused
        r = requests.get(f"{self.base_url}/movies/user1/pass1/3.mkv")
        assert r.status_code == HTTPStatus.TOO_MANY_REQUESTS

        # Non-stream endpoints are not counted
        r = requests.get(f"{self.base_url}/player_api.php?username=user1&password=pass1")
        assert r.status_code == HTTPStatus.OK

        SlowMemoryStream.gate.set()
        t.join(5)
        assert results["first"].status_code == HTTPStatus.OK
        for _ in range(50):  # The slot is released right after the last byte is sent
            if self.server.get_active_stream_count("user1") == 0:
                break
            time.sleep(0.05)
        assert self.server.get_active_stream_count("user1") == 0

        # Slot released -> stream allowed again
        r = requests.get(f"{self.base_url}/movies/user1/pass1/3.mkv")
        assert r.status_code == HTTPStatus.OK

    def test_max_connections_unlimited(self):
        SlowMemoryStream.gate.set()
        for _ in range(3):
            r = requests.get(f"{self.base_url}/movies/user2/pass2/3.mkv")
            assert r.status_code == HTTPStatus.OK

    # ---------------------------------------------------------------- connection cap

    def test_max_concurrent_connections(self):
        server = XTreamCodeServer(self.entry_provider, None, self.credentials, XTreamCodeProxyMemoryRegistry())
        server.setup(bind_port=8088, max_concurrent_connections=1, request_timeout_seconds=2)
        server.start()
        try:
            time.sleep(0.2)
            SlowMemoryStream.gate.clear()
            results = {}

            def holder():
                try:
                    results["first"] = requests.get("http://127.0.0.1:8088/movies/user2/pass2/2.mkv", timeout=10)
                except Exception as e:
                    results["first"] = e

            t = threading.Thread(target=holder)
            t.start()
            for _ in range(50):
                if server.get_active_stream_count("user2") or self.server.get_active_stream_count("user2"):
                    break
                time.sleep(0.05)
            time.sleep(0.2)

            # Second connection is dropped immediately (not queued forever)
            try:
                requests.get("http://127.0.0.1:8088/player_api.php?username=user2&password=pass2", timeout=3)
                refused = False
            except requests.exceptions.RequestException:
                refused = True
            assert refused

            SlowMemoryStream.gate.set()
            t.join(5)
            assert getattr(results["first"], "status_code", None) == HTTPStatus.OK

            # Slot freed -> accepted again
            r = requests.get("http://127.0.0.1:8088/player_api.php?username=user2&password=pass2", timeout=3)
            assert r.status_code == HTTPStatus.OK
        finally:
            SlowMemoryStream.gate.set()
            server.stop()
