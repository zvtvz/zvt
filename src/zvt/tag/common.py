# -*- coding: utf-8 -*-
from enum import Enum


class StockPoolType(Enum):
    system = "system"
    custom = "custom"
    dynamic = "dynamic"


class DynamicPoolType(Enum):
    limit_up = "limit_up"
    limit_down = "limit_down"


class InsertMode(Enum):
    overwrite = "overwrite"
    append = "append"


class TagType(Enum):
    #: A tag is a main tag due to its extensive capacity.
    main_tag = "main_tag"
    sub_tag = "sub_tag"
    hidden_tag = "hidden_tag"


class TagStatsQueryType(Enum):
    simple = "simple"
    details = "details"


# the __all__ is generated
__all__ = ["StockPoolType", "DynamicPoolType", "InsertMode", "TagType", "TagStatsQueryType"]
