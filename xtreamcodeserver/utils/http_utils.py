import ipaddress
import re

class HTTPUtils:

    @staticmethod
    def get_start_offset(http_req_headers: dict) -> int:
        # "Range: bytes = 0 - 499"
        range_begin = None
        range_header = http_req_headers.get("range")
        if range_header:
            range_regex = re.search('bytes=([0-9]*)-([0-9]*)', range_header, re.IGNORECASE)
            if range_regex:
                range_begin = int(range_regex.group(1))
                # range_end = range_regex.group(2)

        return range_begin

    @staticmethod
    def parse_networks(cidr_list: list) -> list:
        """Parses ["192.168.1.0/24", "10.0.0.1", ...] into ip_network objects. Raises ValueError on bad input."""
        networks = []
        for cidr in (cidr_list or []):
            networks.append(ipaddress.ip_network(str(cidr).strip(), strict=False))
        return networks

    @staticmethod
    def is_ip_in_networks(ip: str, networks: list) -> bool:
        try:
            address = ipaddress.ip_address(ip)
        except ValueError:
            return False

        return any(address in network for network in networks)

    @staticmethod
    def get_client_ip(peer_ip: str, x_forwarded_for: str, trusted_proxies: list) -> str:
        """Returns the real client IP.

        peer_ip: address of the TCP peer (what the socket sees).
        x_forwarded_for: value of the X-Forwarded-For header, or None.
        trusted_proxies: ip_network list (see parse_networks) of reverse proxies allowed to set X-Forwarded-For.

        When the peer is not a trusted proxy the header is ignored (a client could forge it).
        Otherwise the header is walked from the right (the last hop appended by our proxy is the most
        trustworthy): the first address that is not itself a trusted proxy is the client.
        """
        if not trusted_proxies or not x_forwarded_for or not HTTPUtils.is_ip_in_networks(peer_ip, trusted_proxies):
            return peer_ip

        hops = [hop.strip() for hop in x_forwarded_for.split(",") if hop.strip()]
        for hop in reversed(hops):
            try:
                ipaddress.ip_address(hop)
            except ValueError:
                return peer_ip  # Malformed header: do not trust any of it

            if not HTTPUtils.is_ip_in_networks(hop, trusted_proxies):
                return hop

        return peer_ip
    