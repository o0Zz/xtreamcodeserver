import requests
from xtreamcodeserver.credentials.credentials import XTreamCodeCredentials
from xtreamcodeserver.providers.inmemory.credentials_provider import XTreamCodeCredentialsMemoryProvider
from xtreamcodeserver.server import XTreamCodeServer

class TestHTTP:
    
    def setup_class(self):
        self.bind_port = 8086
        self.credentials = XTreamCodeCredentialsMemoryProvider()
        self.credentials.add_or_update_credentials(XTreamCodeCredentials("test", "test", None))
        self.server = XTreamCodeServer(None, None, self.credentials, None)
        self.server.setup(bind_port=self.bind_port)
        self.server.start()
        self.test_url = f"http://127.0.0.1:{self.bind_port}/player_api.php?username=test&password=test"
        
    def teardown_class(self):
        self.server.stop()

    def test_get_allow_origin(self):
        r = requests.get(self.test_url)
        assert r.headers["access-control-allow-origin"] == "*"

    def test_options_allow_origin(self):
        r = requests.options(self.test_url)
        assert r.headers["access-control-allow-origin"] == "*"
        
