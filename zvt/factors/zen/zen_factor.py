# -*- coding: utf-8 -*-
from enum import Enum
from typing import List, Union

import pandas as pd

from zvdata import IntervalLevel
from zvdata.factor import StateFactor
from zvt.factors.technical_factor import TechnicalFactor
from zvt.settings import SAMPLE_STOCK_CODES


class ZenState(Enum):
    trending_up = 'trending_up'
    trending_down = 'trending_down'
    shaking = 'shaking'


class ZenStateFactor(TechnicalFactor, StateFactor):
    states = [ZenState.trending_up, ZenState.trending_up, ZenState.shaking]

    def __init__(self,
                 entity_ids: List[str] = None,
                 entity_type: str = 'stock',
                 exchanges: List[str] = ['sh', 'sz'],
                 codes: List[str] = None,
                 the_timestamp: Union[str, pd.Timestamp] = None,
                 start_timestamp: Union[str, pd.Timestamp] = None,
                 end_timestamp: Union[str, pd.Timestamp] = None,
                 columns: List = None,
                 filters: List = None,
                 order: object = None,
                 limit: int = None,
                 provider: str = 'joinquant',
                 level: IntervalLevel = IntervalLevel.LEVEL_1DAY,
                 category_field: str = 'entity_id',
                 time_field: str = 'timestamp',
                 trip_timestamp: bool = True,
                 auto_load: bool = True,
                 fq='qfq',
                 short_window=5,
                 long_window=10) -> None:
        self.short_window = short_window
        self.long_window = long_window

        super().__init__(entity_ids, entity_type, exchanges, codes, the_timestamp, start_timestamp, end_timestamp,
                         columns, filters, order, limit, provider, level, category_field, time_field, trip_timestamp,
                         auto_load, fq, indicators=['ma', 'ma', 'macd'],
                         indicators_param=[{'window': short_window}, {'window': long_window},
                                           {'slow': 26, 'fast': 12, 'n': 9}], valid_window=26)

    def do_compute(self):
        super().do_compute()

        short_ma_col = 'ma{}'.format(self.short_window)
        long_ma_col = 'ma{}'.format(self.long_window)

        self.depth_df['score'] = self.depth_df[short_ma_col] > self.depth_df[long_ma_col]

        for entity_id, df in self.depth_df.groupby('entity_id'):
            count = 0
            area = 0
            current_state = None
            for index, item in df['score'].iteritems():
                # ５日线在１０日线之上
                if item:
                    col = 'up_count'
                    col1 = 'up_area'
                    state = 'up'
                # ５日线在１０日线之下
                else:
                    col = 'down_count'
                    col1 = 'down_area'
                    state = 'down'

                # 计算维持状态的 次数 和相应的 面积
                if current_state == state:
                    count = count + 1
                    area += abs(self.depth_df.loc[index, long_ma_col] - self.depth_df.loc[index, short_ma_col])
                else:
                    current_state = state
                    count = 1
                    area = abs(self.depth_df.loc[index, long_ma_col] - self.depth_df.loc[index, short_ma_col])

                self.depth_df.loc[index, col] = count
                self.depth_df.loc[index, col1] = area
                # 短期均线　长期均线的距离
                self.depth_df.loc[index, 'distance'] = self.depth_df.loc[index, short_ma_col] - self.depth_df.loc[
                    index, long_ma_col]


if __name__ == '__main__':
    factor = ZenStateFactor(codes=SAMPLE_STOCK_CODES, start_timestamp='2007-01-01', end_timestamp='2019-09-29',
                            level=IntervalLevel.LEVEL_1WEEK)

    print(factor.depth_df[['down_count', 'up_count']].groupby('entity_id').describe())
    print(factor.depth_df[['down_area', 'up_area']].groupby('entity_id').describe())
