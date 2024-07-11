import logging
import zlib
from xtreamcodeserver.entry.entry import *
from collections import UserDict as DictClass

from xtreamcodeserver.entry.entry import XTreamCodeEntry, XTreamCodeType

_LOGGER = logging.getLogger(__name__)

class XTreamCodeContainer(DictClass):
    def __init__(self, name: str, type: XTreamCodeType, entry_id: int=None, extra_id: int=0):
        self.m_id = entry_id
        self.m_type = type
        self.m_name = name
        
        if self.m_id == None:
            self.m_id = zlib.crc32(("%s#%d#%d" % (name, type, extra_id)).encode('utf-8')) & XTREAMCODE_ID_MAX_VALUE  # If the id is not provided use a crc of the crc of the name as ID to be able to have everytime the same id
        if self.m_id > XTREAMCODE_ID_MAX_VALUE:
            _LOGGER.error("Invalid entry ID (%d), ID value bigger than the maximum allowed (%d)" % (self.m_id, XTREAMCODE_ID_MAX_VALUE))

        self.m_entry_list = {}

    def get_type(self) -> XTreamCodeType:
        return self.m_type
        
    def get_name(self) -> str:
        return self.m_name

    def get_entry_id(self) -> int:
        return self.m_id

    def is_container(self) -> bool:
        return True
    
    def get_entries(self) -> list[XTreamCodeEntry]:
        return list(self.m_entry_list.values())
    
    ################################################
    # Override dict functions
    ################################################

    def __len__(self) -> int:
        return len(self.m_entry_list)

    def __getitem__(self, key) -> XTreamCodeEntry:
        return self.m_entry_list[key.get_entry_id()]
  
    def __setitem__(self, key, item: XTreamCodeEntry):

            #Make sure we add correct type to correct entry type according to categorie type
        if (item.get_type() != self.get_type()) and (item.get_type() != XTreamCodeType.EPISODE and self.get_type() != XTreamCodeType.SERIE):
            _LOGGER.error("Error: Invalid entry type (%s) for container type (%s) (Entry name: %s)" % (item.get_type(), self.get_type(), item.get_name()))
            raise ValueError("Invalid entry type (%s) for container (%s) (Entry: %s)" % (item.get_type(), self.get_type(), item.get_name()))
        
        self.m_entry_list[key.get_entry_id()] = item

    def __delitem__(self, key):
        del self.m_entry_list[key.get_entry_id()]

    def __iter__(self):
        return iter(self.m_entry_list)
  
    def __contains__(self, key):
        if key.get_entry_id() in self.m_entry_list:
            return True
        return False

    def __repr__(self):
        return repr(self.m_entry_list)

    def __or__(self, other):
        raise NotImplementedError

    def __ror__(self, other):
        raise NotImplementedError

    def __ior__(self, other):
        raise NotImplementedError

    def __copy__(self):
        raise NotImplementedError

    def copy(self):
        raise NotImplementedError


