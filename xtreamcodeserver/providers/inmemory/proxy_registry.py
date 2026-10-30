import logging
import secrets
import threading
from collections import OrderedDict

from xtreamcodeserver.interfaces.proxyregistry import IXTreamCodeProxyRegistry

_LOGGER = logging.getLogger(__name__)


class XTreamCodeProxyMemoryRegistry(IXTreamCodeProxyRegistry):
    """In-memory, thread-safe, LRU bounded implementation of IXTreamCodeProxyRegistry.

    Tokens are random (secrets.token_urlsafe) and carry no information about the URL.
    Tokens do not survive a restart: HLS players refetch the playlist every few seconds
    and get fresh ones.
    """

    def __init__(self, max_entries: int = 4096):
        self.m_lock = threading.Lock()
        self.m_max_entries = max(1, int(max_entries))
        self.m_token_to_url = OrderedDict()
        self.m_url_to_token = {}

    def register(self, url: str) -> str:
        with self.m_lock:
            token = self.m_url_to_token.get(url)
            if token is not None:
                self.m_token_to_url.move_to_end(token)
                return token

            token = secrets.token_urlsafe(16)
            while token in self.m_token_to_url:
                token = secrets.token_urlsafe(16)

            self.m_token_to_url[token] = url
            self.m_url_to_token[url] = token

            while len(self.m_token_to_url) > self.m_max_entries:
                _old_token, old_url = self.m_token_to_url.popitem(last=False)
                self.m_url_to_token.pop(old_url, None)

            return token

    def resolve(self, token: str) -> str:
        if not token:
            return None

        with self.m_lock:
            url = self.m_token_to_url.get(token)
            if url is not None:
                self.m_token_to_url.move_to_end(token)
            return url

    def clear(self) -> None:
        with self.m_lock:
            self.m_token_to_url.clear()
            self.m_url_to_token.clear()

    def __len__(self) -> int:
        with self.m_lock:
            return len(self.m_token_to_url)
