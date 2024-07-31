# -*- coding: utf-8 -*-
import math

import pandas as pd

from zvt.contract import IntervalLevel
from zvt.utils.time_utils import to_pd_timestamp


def is_in_same_interval(t1: pd.Timestamp, t2: pd.Timestamp, level: IntervalLevel):
    t1 = to_pd_timestamp(t1)
    t2 = to_pd_timestamp(t2)
    if level == IntervalLevel.LEVEL_1WEEK:
        return t1.week == t2.week
    if level == IntervalLevel.LEVEL_1MON:
        return t1.month == t2.month

    return level.floor_timestamp(t1) == level.floor_timestamp(t2)


def evaluate_size_from_timestamp(
    start_timestamp, level: IntervalLevel, one_day_trading_minutes, end_timestamp: pd.Timestamp = None
):
    """
    given from timestamp,level,one_day_trading_minutes,this func evaluate size of kdata to current.
    it maybe a little bigger than the real size for fetching all the kdata.

    :param start_timestamp:
    :type start_timestamp: pd.Timestamp
    :param level:
    :type level: IntervalLevel
    :param one_day_trading_minutes:
    :type one_day_trading_minutes: int
    """
    if not end_timestamp:
        end_timestamp = pd.Timestamp.now()
    else:
        end_timestamp = to_pd_timestamp(end_timestamp)

    time_delta = end_timestamp - to_pd_timestamp(start_timestamp)

    one_day_trading_seconds = one_day_trading_minutes * 60

    if level == IntervalLevel.LEVEL_1DAY:
        return time_delta.days + 1

    if level == IntervalLevel.LEVEL_1WEEK:
        return int(math.ceil(time_delta.days / 7)) + 1

    if level == IntervalLevel.LEVEL_1MON:
        return int(math.ceil(time_delta.days / 30)) + 1

    if time_delta.days > 0:
        seconds = (time_delta.days + 1) * one_day_trading_seconds
        return int(math.ceil(seconds / level.to_second())) + 1
    else:
        seconds = time_delta.total_seconds()
        return min(int(math.ceil(seconds / level.to_second())) + 1, one_day_trading_seconds / level.to_second() + 1)


def next_timestamp_on_level(current_timestamp: pd.Timestamp, level: IntervalLevel) -> pd.Timestamp:
    current_timestamp = to_pd_timestamp(current_timestamp)
    return current_timestamp + pd.Timedelta(seconds=level.to_second())


def is_finished_kdata_timestamp(timestamp, level: IntervalLevel):
    timestamp = to_pd_timestamp(timestamp)
    if level.floor_timestamp(timestamp) == timestamp:
        return True
    return False
