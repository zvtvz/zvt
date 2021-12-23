# -*- coding: utf-8 -*-
from enum import Enum


class BehaviorCategory(Enum):
    # 上涨
    up = 1
    # 下跌
    down = -1


class RelativePerformance(Enum):
    # 表现比90%好
    best = 0.9
    ordinary = 0.5
    poor = 0


# the __all__ is generated
__all__ = ["BehaviorCategory", "RelativePerformance"]
