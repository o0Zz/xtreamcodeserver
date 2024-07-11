import logging
from xtreamcodeserver.entry.container import *
from xtreamcodeserver.entry.entry import XTreamCodeType

_LOGGER = logging.getLogger(__name__)

class XTreamCodeCategory(XTreamCodeContainer):
    def __init__(self, name: str, category_type: XTreamCodeType, category_id: int=None):
        XTreamCodeContainer.__init__(self, name, XTreamCodeType.CATEGORY, category_id, 0)
        self.m_category_type = category_type

    def get_type(self) -> XTreamCodeType:
        return self.m_category_type
    
    def add_entry(self, entry: XTreamCodeEntry) -> None:
        entry.add_category_id(self.m_id)
        self[entry] = entry

    def get_json(self) -> dict:
        ret = {
            "category_id": str(self.m_id),
            "category_name": self.m_name,
            "parent_id": 0
        }

        return ret
