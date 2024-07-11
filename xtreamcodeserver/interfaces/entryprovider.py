
from abc import abstractmethod
from xtreamcodeserver.entry.category import XTreamCodeCategory
from xtreamcodeserver.entry.entry import XTreamCodeEntry, XTreamCodeType

class IXTreamCodeEntryProvider:

    @abstractmethod
    def get_entry(self, entry_id: int) -> XTreamCodeEntry:
        raise NotImplementedError("Must be implemented by Subclasses !")

    @abstractmethod
    def get_entries(self, category_type: XTreamCodeType=None, category_id: int=None) -> list[XTreamCodeEntry]:
        raise NotImplementedError("Must be implemented by Subclasses !")

    @abstractmethod
    def get_category(self, category_id: int=None) -> XTreamCodeCategory:
        raise NotImplementedError("Must be implemented by Subclasses !")
    
    @abstractmethod
    def get_categories(self, type: XTreamCodeType) -> list[XTreamCodeCategory]:
        raise NotImplementedError("Must be implemented by Subclasses !")