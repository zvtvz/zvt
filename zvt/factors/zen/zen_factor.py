# -*- coding: utf-8 -*-
import argparse
import os
from enum import Enum
from typing import List, Union

import pandas as pd

from zvdata import IntervalLevel
from zvdata.factor import StateFactor
from zvdata.utils.time_utils import now_pd_timestamp
from zvt import DATA_PATH
from zvt.api import get_entities, Stock
from zvt.factors.technical_factor import TechnicalFactor


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
                         auto_load, fq=fq, indicators=['ma', 'ma'],
                         indicators_param=[{'window': short_window}, {'window': long_window}], valid_window=long_window)

    def do_compute(self):
        # call this to calculating the declared indicators
        super().do_compute()

        short_ma_col = 'ma{}'.format(self.short_window)
        long_ma_col = 'ma{}'.format(self.long_window)

        self.depth_df['score'] = self.depth_df[short_ma_col] > self.depth_df[long_ma_col]

        for entity_id, df in self.depth_df.groupby('entity_id'):
            count = 0
            area = 0
            current_state = None
            pre_index = None
            pre_col_total = None
            for index, item in df['score'].iteritems():
                # ５日线在１０日线之上
                if item:
                    col_current = 'up_current_count'
                    col_area = 'up_current_area'
                    col_total = 'up_total_count'
                    state = 'up'
                # ５日线在１０日线之下
                elif not pd.isna(df[short_ma_col][index]) and not pd.isna(df[long_ma_col][index]):
                    col_current = 'down_current_count'
                    col_area = 'down_current_area'
                    col_total = 'down_total_count'
                    state = 'down'
                else:
                    continue

                # 计算维持状态的 次数 和相应的 面积
                if current_state == state:
                    count = count + 1
                    area += abs(self.depth_df.loc[index, long_ma_col] - self.depth_df.loc[index, short_ma_col])
                else:
                    # change state,set pre state total count
                    if count > 0:
                        self.depth_df.loc[pre_index, pre_col_total] = count
                    current_state = state
                    count = 1
                    area = abs(self.depth_df.loc[index, long_ma_col] - self.depth_df.loc[index, short_ma_col])

                self.depth_df.loc[index, col_current] = count
                self.depth_df.loc[index, col_area] = area

                pre_index = index
                pre_col_total = col_total

                # 短期均线　长期均线的距离
                # self.depth_df.loc[index, 'distance'] = abs(self.depth_df.loc[index, short_ma_col] - self.depth_df.loc[
                #     index, long_ma_col]) / self.depth_df.loc[index, long_ma_col]

            self.logger.info('finish calculating :{}'.format(entity_id))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--level', help='trading level', default='1d', choices=[item.value for item in IntervalLevel])
    parser.add_argument('--start', help='start code', default='000001')
    parser.add_argument('--end', help='end code', default='000005')

    args = parser.parse_args()

    level = IntervalLevel(args.level)
    start = args.start
    end = args.end

    entities = get_entities(provider='eastmoney', entity_type='stock', columns=[Stock.entity_id, Stock.code],
                            filters=[Stock.code >= start, Stock.code < end])

    codes = entities.index.to_list()

    factor = ZenStateFactor(codes=codes, start_timestamp='2005-01-01',
                            end_timestamp=now_pd_timestamp(),
                            level=level)

    if not os.path.exists(os.path.join(DATA_PATH, 'zen')):
        os.makedirs(os.path.join(DATA_PATH, 'zen'))

    path = os.path.join(DATA_PATH, 'zen', f'{start}_{end}_{level}.csv')

    factor.depth_df[['ma5',
                     'ma10',
                     'score',
                     'down_current_count',
                     'down_current_area',
                     'down_total_count',
                     'up_total_count',
                     'up_current_count',
                     'up_current_area']
    ].to_csv(path)
