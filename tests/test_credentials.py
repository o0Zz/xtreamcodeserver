import requests
import datetime
from http import HTTPStatus
from xtreamcodeserver.credentials.credentials import XTreamCodeCredentials
from xtreamcodeserver.providers.inmemory.credentials_provider import XTreamCodeCredentialsMemoryProvider
from xtreamcodeserver.server import XTreamCodeDefaultDateTimeProvider, XTreamCodeServer

class TestCredentials:

    def setup_class(self):
        self.bind_port = 8081
        self.credentials = XTreamCodeCredentialsMemoryProvider()
        self.datetime_provider = XTreamCodeDefaultDateTimeProvider()
        self.server = XTreamCodeServer(None, None, self.credentials, self.datetime_provider)
        self.server.setup(bind_port=self.bind_port)
        self.server.start()
        self.test_url = f"http://127.0.0.1:{self.bind_port}/player_api.php?username=test&password=test"
        
    def teardown_class(self):
        self.server.stop()

    def test_valid_credentials_without_expiration(self):
        self.credentials.add_or_update_credentials(XTreamCodeCredentials("test", "test"))
        r = requests.get(self.test_url)
        assert r.status_code == HTTPStatus.OK

    def test_valid_credentials_with_expiration(self):
        self.credentials.add_or_update_credentials(XTreamCodeCredentials("test", "test", self.datetime_provider.utcnow() + datetime.timedelta(days=1)))
        r = requests.get(self.test_url)
        assert r.status_code == HTTPStatus.OK

    def test_credentials_expired(self):
        self.credentials.add_or_update_credentials(XTreamCodeCredentials("test", "test", self.datetime_provider.utcnow() - datetime.timedelta(days=1)))
        r = requests.get(self.test_url)
        assert r.status_code == HTTPStatus.UNAUTHORIZED