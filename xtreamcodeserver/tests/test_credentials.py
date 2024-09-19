import base64
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
        self.test_url_query = f"http://127.0.0.1:{self.bind_port}/player_api.php?username=test&password=test"
        b64_url = base64.b64encode(f'http://127.0.0.1:{self.bind_port}/test/test/'.encode('utf-8')).decode('utf-8')
        self.test_url_proxy = f"http://127.0.0.1:{self.bind_port}/proxy/test/test/{b64_url}/xmltv.php"
        
    def teardown_class(self):
        self.server.stop()

    def test_valid_credentials_without_expiration(self):
        self.credentials.add_or_update_credentials(XTreamCodeCredentials("test", "test"))
        r = requests.get(self.test_url_query)
        assert r.status_code == HTTPStatus.OK

    def test_valid_credentials_with_expiration(self):
        self.credentials.add_or_update_credentials(XTreamCodeCredentials("test", "test", self.datetime_provider.utcnow() + datetime.timedelta(days=1)))
        r = requests.get(self.test_url_query)
        assert r.status_code == HTTPStatus.OK

    def test_credentials_expired(self):
        self.credentials.add_or_update_credentials(XTreamCodeCredentials("test", "test", self.datetime_provider.utcnow() - datetime.timedelta(days=1)))
        r = requests.get(self.test_url_query)
        assert r.status_code == HTTPStatus.UNAUTHORIZED

    def test_credentials_proxy(self):
        self.credentials.add_or_update_credentials(XTreamCodeCredentials("test", "test", self.datetime_provider.utcnow() + datetime.timedelta(days=1)))
        r = requests.get(self.test_url_proxy)
        assert r.status_code != HTTPStatus.UNAUTHORIZED
                                                                         