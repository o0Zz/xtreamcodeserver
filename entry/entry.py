import zlib
import logging

_LOGGER = logging.getLogger(__name__)

# Below value has been determined with "Android Smarters Player" (This player reject all ID greater than that)
XTREAMCODE_ID_MAX_VALUE = 0x7FFFFFFF

class XTreamCodeType:
    UNKNOWN = 0
    CATEGORY = 1
    VOD = 2
    LIVE = 3
    SERIE = 4
    SEASON = 5
    EPISODE = 6

class XTreamCodeEntry:
    def __init__(self, name: str, type: XTreamCodeType, entry_id: int=None, extra_id: int=0):
        self.m_id = entry_id
        self.m_type = type
        self.m_name = name
        
        if self.m_id == None:
            self.m_id = zlib.crc32(("%s/%d/%d" % (name, type, extra_id)).encode('utf-8')) & XTREAMCODE_ID_MAX_VALUE  # If the id is not provided use a crc of the crc of the name as ID to be able to have everytime the same id
        if self.m_id > XTREAMCODE_ID_MAX_VALUE:
            _LOGGER.error("Invalid entry ID (%d), ID value bigger than the maximum allowed (%d)" % (self.m_id, XTREAMCODE_ID_MAX_VALUE))

    def __repr__(self):
        return "%s (%s)" % (self.m_name, self.m_type)
    
    def get_type(self) -> XTreamCodeType:
        return self.m_type
        
    def get_name(self) -> str:
        return self.m_name

    def get_entry_id(self) -> int:
        return self.m_id

    def is_container(self) -> bool:
        return False
