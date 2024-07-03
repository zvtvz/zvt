# -*- coding: utf-8 -*-
from enum import Enum


class StockPoolType(Enum):
    system = "system"
    custom = "custom"


class TagType(Enum):
    main_tag = "main_tag"
    sub_tag = "sub_tag"
    hidden_tag = "hidden_tag"


class TagStatsQueryType(Enum):
    simple = "simple"
    details = "details"


# the __all__ is generated
__all__ = ["StockPoolType", "TagType", "TagStatsQueryType"]
