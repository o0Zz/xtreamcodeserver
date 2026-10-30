from abc import abstractmethod


class IXTreamCodeProxyRegistry:
    """Maps opaque tokens to upstream base URLs for the /proxy/<user>/<pass>/<token>/<file> route.

    The playlist proxy (XTreamCodePlaylistProxyStream) registers the upstream location of every
    HLS segment it rewrites and the HTTP server resolves the token back when the client fetches
    the segment. Only URLs registered through this interface can be reached through /proxy/, and
    the upstream URL (with the provider credentials it may contain) is never exposed to clients.

    The same instance must be shared by the server and by every playlist proxy stream it serves.
    """

    @abstractmethod
    def register(self, url: str) -> str:
        """Returns the token for `url`, creating it if needed. Same url => same token."""
        raise NotImplementedError("Must be implemented by Subclasses !")

    @abstractmethod
    def resolve(self, token: str) -> str:
        """Returns the url registered for `token`, or None when the token is unknown."""
        raise NotImplementedError("Must be implemented by Subclasses !")
