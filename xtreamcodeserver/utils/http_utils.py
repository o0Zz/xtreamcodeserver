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
    