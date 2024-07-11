import logging
import threading
from xtreamcodeserver.entry.category import XTreamCodeCategory
from xtreamcodeserver.entry.container import XTreamCodeContainer
from xtreamcodeserver.entry.entry import XTreamCodeEntry, XTreamCodeType
from xtreamcodeserver.interfaces.entryprovider import IXTreamCodeEntryProvider

_LOGGER = logging.getLogger(__name__)

class XTreamCodeEntryMemoryProvider(IXTreamCodeEntryProvider):

    def __init__(self):
        self.m_lock = threading.RLock()
        self.m_categories = {}

    # ------------------------------------------------------------

    def get_entry(self, entry_id: int) -> XTreamCodeEntry:
        return self.__get_entry(entry_id)

    # ------------------------------------------------------------
    
    def get_entries(self, category_type: XTreamCodeType=None, category_id: int=None) -> list[XTreamCodeEntry]:
        entry_list = []
        with self.m_lock:
            for _category_id, category in self.m_categories.items():
                if (category_id is None) or int(category_id) == _category_id:
                    if (category_type is None) or category.get_type() == category_type:
                        entry_list.extend(category.get_entries())

        return entry_list
     
    # ------------------------------------------------------------

    def get_category(self, category_id: int=None) -> XTreamCodeCategory:
        with self.m_lock:
            if category_id in self.m_categories:
                return  self.m_categories[category_id]
        return None
    
    # ------------------------------------------------------------

    def get_categories(self, type: XTreamCodeType) -> list[XTreamCodeCategory]:
        category_list = []

        with self.m_lock:
            for category_id, category in self.m_categories.items():
                if category.get_type() == type:
                    category_list.append(category.get_json())

        return category_list
   
    # ------------------------------------------------------------

    def clear_categories(self) -> None:
        with self.m_lock:
            self.m_categories.clear()

    # ------------------------------------------------------------

    def set_categories(self, category_list: dict[int, XTreamCodeCategory]) -> None:
        with self.m_lock:
            self.m_categories.clear()
            for category_id, category in category_list.items():
                self.m_categories[category.get_entry_id()] = category

    # ------------------------------------------------------------

    def add_category(self, category: XTreamCodeCategory) -> None:
        with self.m_lock:
            self.m_categories[category.get_entry_id()] = category

    # ------------------------------------------------------------

    def __get_entry(self, entry_id: int, container: XTreamCodeContainer=None) -> XTreamCodeEntry:
        
        with self.m_lock:

            if container == None:
                entries = []
                for category_id, category in self.m_categories.items():
                    entries.append(category)
            else:
                entries = container.get_entries()

            for entry in entries:
                if entry.get_entry_id() == int(entry_id):
                    return entry
                
                if entry.is_container(): # Recursive search in sub containers
                    ret = self.__get_entry(entry_id, entry)
                    if ret:
                        return ret
                    
        return None