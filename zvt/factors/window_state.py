# -*- coding: utf-8 -*-
from zvt.api import get_kdata, get_kdata_schema
from zvt.contract import IntervalLevel
from zvt.domain import Stock


class WindowState(object):
    shaking_low = False
    std_low = False

    def __init__(self,
                 entity_id,
                 timestamp,
                 window=100,
                 level=IntervalLevel.LEVEL_1DAY,
                 entity_schema=Stock,
                 range=0.3,
                 std=1) -> None:
        self.entity_id = entity_id
        self.window = window

        data_schema = get_kdata_schema(entity_schema.__name__, level=level)

        self.df = get_kdata(entity_id=entity_id, level=level, end_timestamp=timestamp,
                            order=data_schema.timestamp.desc(),
                            limit=window, columns=['volume', 'open', 'close', 'high', 'low'])
        self.range = range
        self.std = std

    def calculate_state(self):
        s = self.df['close'].describe()
        # count    3.0
        # mean     2.0
        # std      1.0
        # min      1.0
        # 25%      1.5
        # 50%      2.0
        # 75%      2.5
        # max      3.0
        s['mean']
        range = (s['max'] - s['min']) / s['min']
        self.shaking_low = range < self.range
        self.std_low = s['std'] < self.std
