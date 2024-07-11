import requests
import datetime
from xtreamcodeserver.credentials.credentials import XTreamCodeCredentials
from xtreamcodeserver.interfaces.datetimeprovider import IXTreamCodeDateTimeProvider
from xtreamcodeserver.providers.inmemory.credentials_provider import XTreamCodeCredentialsMemoryProvider
from xtreamcodeserver.server import XTreamCodeServer

class DateTimeProviderTest(IXTreamCodeDateTimeProvider):
    def __init__(self) -> None:
        self.dt = datetime.datetime(year=2024, month=1, day=1, tzinfo=datetime.timezone.utc)

    def utcnow(self) -> datetime.datetime:
        return self.dt
    
class TestInfos:
    
    def setup_class(self):
        self.bind_port = 8084
        self.credentials = XTreamCodeCredentialsMemoryProvider()
        self.datetime_provider = DateTimeProviderTest()
        self.server = XTreamCodeServer(None, None, self.credentials, self.datetime_provider)
        self.server.setup(bind_port=self.bind_port)
        self.server.start()
        self.test_url = f"http://127.0.0.1:{self.bind_port}/player_api.php?username=test&password=test"
        
    def teardown_class(self):
        self.server.stop()

    def test_correct_expiration_date(self):
        self.credentials.add_or_update_credentials(XTreamCodeCredentials("test", "test", datetime.datetime(year=2034, month=1, day=1, tzinfo=datetime.timezone.utc)))
        r = requests.get(self.test_url)
        assert r.json()["user_info"]["exp_date"] == 2019686400

    def test_correct_user_info(self):
        self.credentials.add_or_update_credentials(XTreamCodeCredentials("test", "test"))
        r = requests.get(self.test_url)
        assert r.json()["user_info"] == {
            "username": "test",
            "password": "test",
            "message": "",
            "auth": 1,
            "status": "Active",
            "is_trial": 0,
            "active_cons": 0,
            "created_at": 0,
            "max_connections": 1,
            "allowed_output_formats": ["m3u8", "ts"]
        }

    def test_correct_server_info(self):
        self.credentials.add_or_update_credentials(XTreamCodeCredentials("test", "test"))
        r = requests.get(self.test_url)
        assert r.json()["server_info"]["port"] == str(self.bind_port)
        assert r.json()["server_info"]["https_port"] == str(self.bind_port)
        assert r.json()["server_info"]["server_protocol"] == "http"
        assert r.json()["server_info"]["rtmp_port"] == "0"
        assert r.json()["server_info"]["timezone"] == "GMT"
        assert r.json()["server_info"]["timestamp_now"] == 1704067200
        assert r.json()["server_info"]["time_now"] == "2024-01-01 00:00:00"
        
