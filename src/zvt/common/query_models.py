# -*- coding: utf-8 -*-
from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class OrderByType(Enum):
    asc = "asc"
    desc = "desc"


class TimeUnit(Enum):
    year = "year"
    month = "month"
    day = "day"
    hour = "hour"
    minute = "minute"
    second = "second"


class AbsoluteTimeRange(BaseModel):
    start_timestamp: datetime
    end_timestamp: datetime


class RelativeTimeRage(BaseModel):
    interval: int
    time_unit: TimeUnit


class TimeRange(BaseModel):
    absolute_time_range: Optional[AbsoluteTimeRange] = Field(default=None)
    relative_time_range: Optional[RelativeTimeRage] = Field(default=None)


# the __all__ is generated
__all__ = ["OrderByType", "TimeUnit", "AbsoluteTimeRange", "RelativeTimeRage", "TimeRange"]
