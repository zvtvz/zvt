# -*- coding: utf-8 -*-
import enum
import math

import pandas as pd
from sqlalchemy import Column, String, DateTime

from zvdata.utils.time_utils import now_pd_timestamp


class Mixin(object):
    id = Column(String, primary_key=True)
    entity_id = Column(String)

    # the meaning could be different for different case,most of time it means 'happen time'
    timestamp = Column(DateTime)


class NormalMixin(Mixin):
    # the record created time in db
    created_timestamp = Column(DateTime, default=now_pd_timestamp())
    # the record updated time in db, some recorder would check it for whether need to refresh
    updated_timestamp = Column(DateTime)


class EntityMixin(Mixin):
    entity_type = Column(String(length=64))
    exchange = Column(String(length=32))
    code = Column(String(length=64))
    name = Column(String(length=128))


class NormalEntityMixin(EntityMixin):
    # the record created time in db
    created_timestamp = Column(DateTime, default=now_pd_timestamp())
    # the record updated time in db, some recorder would check it for whether need to refresh
    updated_timestamp = Column(DateTime)


class IntervalLevel(enum.Enum):
    LEVEL_TICK = 'tick'
    LEVEL_1MIN = '1m'
    LEVEL_5MIN = '5m'
    LEVEL_15MIN = '15m'
    LEVEL_30MIN = '30m'
    LEVEL_1HOUR = '1h'
    LEVEL_4HOUR = '4h'
    LEVEL_1DAY = '1d'
    LEVEL_1WEEK = '1wk'

    def to_pd_freq(self):
        if self == IntervalLevel.LEVEL_1MIN:
            return '1min'
        if self == IntervalLevel.LEVEL_5MIN:
            return '5min'
        if self == IntervalLevel.LEVEL_15MIN:
            return '15min'
        if self == IntervalLevel.LEVEL_30MIN:
            return '30min'
        if self == IntervalLevel.LEVEL_1HOUR:
            return '1H'
        if self == IntervalLevel.LEVEL_4HOUR:
            return '4H'
        if self >= IntervalLevel.LEVEL_1DAY:
            return '1D'

    def count_from_timestamp(self, pd_timestamp, one_day_trading_minutes):
        current_time = pd.Timestamp.now()
        time_delta = current_time - pd_timestamp

        one_day_trading_seconds = one_day_trading_minutes * 60

        if time_delta.days > 0:
            seconds = (time_delta.days + 1) * one_day_trading_seconds
            return None, int(math.ceil(seconds / self.to_second())) + 1
        else:
            seconds = time_delta.total_seconds()
            return self.to_second() - seconds, min(int(math.ceil(seconds / self.to_second())) + 1,
                                                   one_day_trading_seconds / self.to_second())

    def floor_timestamp(self, pd_timestamp):
        if self == IntervalLevel.LEVEL_1MIN:
            return pd_timestamp.floor('1min')
        if self == IntervalLevel.LEVEL_5MIN:
            return pd_timestamp.floor('5min')
        if self == IntervalLevel.LEVEL_15MIN:
            return pd_timestamp.floor('15min')
        if self == IntervalLevel.LEVEL_30MIN:
            return pd_timestamp.floor('30min')
        if self == IntervalLevel.LEVEL_1HOUR:
            return pd_timestamp.floor('1h')
        if self == IntervalLevel.LEVEL_4HOUR:
            return pd_timestamp.floor('4h')
        if self >= IntervalLevel.LEVEL_1DAY:
            return pd_timestamp.floor('1d')

    def is_last_data_of_day(self, hour, minute, pd_timestamp):
        if self == IntervalLevel.LEVEL_1MIN:
            return pd_timestamp.hour == hour and pd_timestamp.minute + 1 == minute
        if self == IntervalLevel.LEVEL_5MIN:
            return pd_timestamp.hour == hour and pd_timestamp.minute + 5 == minute
        if self == IntervalLevel.LEVEL_15MIN:
            return pd_timestamp.hour == hour and pd_timestamp.minute + 15 == minute
        if self == IntervalLevel.LEVEL_30MIN:
            return pd_timestamp.hour == hour and pd_timestamp.minute + 30 == minute
        if self == IntervalLevel.LEVEL_1HOUR:
            return pd_timestamp.hour == hour and pd_timestamp.minute + 60 == minute
        if self == IntervalLevel.LEVEL_4HOUR:
            return pd_timestamp.hour == hour and pd_timestamp.minute + 240 == minute
        if self >= IntervalLevel.LEVEL_1DAY:
            return True

    def to_minute(self):
        return int(self.to_second() / 60)

    def to_second(self):
        return int(self.to_ms() / 1000)

    def to_ms(self):
        # we treat tick intervals is 5s, you could change it
        if self == IntervalLevel.LEVEL_TICK:
            return 5 * 1000
        if self == IntervalLevel.LEVEL_1MIN:
            return 60 * 1000
        if self == IntervalLevel.LEVEL_5MIN:
            return 5 * 60 * 1000
        if self == IntervalLevel.LEVEL_15MIN:
            return 15 * 60 * 1000
        if self == IntervalLevel.LEVEL_30MIN:
            return 30 * 60 * 1000
        if self == IntervalLevel.LEVEL_1HOUR:
            return 60 * 60 * 1000
        if self == IntervalLevel.LEVEL_4HOUR:
            return 4 * 60 * 60 * 1000
        if self == IntervalLevel.LEVEL_1DAY:
            return 24 * 60 * 60 * 1000
        if self == IntervalLevel.LEVEL_1WEEK:
            return 7 * 24 * 60 * 60 * 1000

    def __ge__(self, other):
        if self.__class__ is other.__class__:
            return self.to_ms() >= other.to_ms()
        return NotImplemented

    def __gt__(self, other):

        if self.__class__ is other.__class__:
            return self.to_ms() > other.to_ms()
        return NotImplemented

    def __le__(self, other):
        if self.__class__ is other.__class__:
            return self.to_ms() <= other.to_ms()
        return NotImplemented

    def __lt__(self, other):
        if self.__class__ is other.__class__:
            return self.to_ms() < other.to_ms()
        return NotImplemented
