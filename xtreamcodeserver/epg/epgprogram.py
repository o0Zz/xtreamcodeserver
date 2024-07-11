import logging
import datetime

_LOGGER = logging.getLogger(__name__)

class XTreamCodeEPGProgram:
    def __init__(self, datetime_start: datetime.datetime, datetime_stop: datetime.datetime, title: str="", desc: str=""):
        # Convert time to UTC first ! some players do not properly handle timezone different to UTC
        self.m_datetime_start_utc = datetime_start.astimezone(datetime.timezone.utc)
        self.m_datetime_stop_utc = datetime_stop.astimezone(datetime.timezone.utc)
        self.m_title = title
        self.m_desc = desc

    def get_datetime_start_utc(self) -> datetime.datetime:
        return self.m_datetime_start_utc

    def get_datetime_stop_utc(self) -> datetime.datetime:
        return self.m_datetime_stop_utc

    def get_title(self) -> str:
        return self.m_title

    def get_desc(self) -> str:
        return self.m_desc

