# -*- coding: utf-8 -*-
import argparse
from typing import List, Union

import pandas as pd
from sqlalchemy import Column, String, Float, Integer
from sqlalchemy.ext.declarative import declarative_base

from zvdata import IntervalLevel, Mixin
from zvdata.scorer import Transformer
from zvdata.utils.time_utils import now_pd_timestamp
from zvt import register_schema
from zvt.api import get_entities, Stock
from zvt.factors.technical_factor import TechnicalFactor, MaTransformer

# 均线状态统计
MaStateStatsBase = declarative_base()


class MaStateStats(MaStateStatsBase, Mixin):
    __tablename__ = 'ma_state_stats'

    code = Column(String(length=32))
    name = Column(String(length=32))

    ma5 = Column(Float)
    ma10 = Column(Float)
    score = Column(Float)

    down_current_count = Column(Integer)
    down_current_area = Column(Float)
    down_total_count = Column(Integer)

    up_total_count = Column(Integer)
    up_current_count = Column(Float)
    up_current_area = Column(Integer)


register_schema(providers=['zvt'], db_name='ma_stats', schema_base=MaStateStatsBase)


class MaStateStas(TechnicalFactor):
    factor_schema = MaStateStats

    def __init__(self, entity_ids: List[str] = None, entity_type: str = 'stock',
                 exchanges: List[str] = ['sh', 'sz'], codes: List[str] = None,
                 the_timestamp: Union[str, pd.Timestamp] = None, start_timestamp: Union[str, pd.Timestamp] = None,
                 end_timestamp: Union[str, pd.Timestamp] = None, columns: List = None, filters: List = None,
                 order: object = None, limit: int = None, provider: str = 'joinquant',
                 level: Union[str, IntervalLevel] = IntervalLevel.LEVEL_1DAY, category_field: str = 'entity_id',
                 time_field: str = 'timestamp', auto_load: bool = True, valid_window: int = 250,
                 keep_all_timestamp: bool = False, fill_method: str = 'ffill', effective_number: int = 10,
                 transformers: List[Transformer] = [MaTransformer()], need_persist: bool = True) -> None:
        super().__init__(entity_ids, entity_type, exchanges, codes, the_timestamp, start_timestamp,
                         end_timestamp, columns, filters, order, limit, provider, level, category_field, time_field,
                         auto_load, valid_window, keep_all_timestamp, fill_method, effective_number, transformers,
                         need_persist)

    def do_compute(self):
        # call this to calculating the declared indicators
        super().do_compute()

        short_ma_col = 'ma{}'.format(self.short_window)
        long_ma_col = 'ma{}'.format(self.long_window)

        self.pipe_df['score'] = self.pipe_df[short_ma_col] > self.pipe_df[long_ma_col]

        for entity_id, df in self.pipe_df.groupby('entity_id'):
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
                    area += abs(self.pipe_df.loc[index, long_ma_col] - self.pipe_df.loc[index, short_ma_col])
                else:
                    # change state,set pre state total count
                    if count > 0:
                        self.pipe_df.loc[pre_index, pre_col_total] = count
                    current_state = state
                    count = 1
                    area = abs(self.pipe_df.loc[index, long_ma_col] - self.pipe_df.loc[index, short_ma_col])

                self.pipe_df.loc[index, col_current] = count
                self.pipe_df.loc[index, col_area] = area

                pre_index = index
                pre_col_total = col_total

                # 短期均线　长期均线的距离
                # self.pipe_df.loc[index, 'distance'] = abs(self.pipe_df.loc[index, short_ma_col] - self.pipe_df.loc[
                #     index, long_ma_col]) / self.pipe_df.loc[index, long_ma_col]

            self.logger.info('finish calculating :{}'.format(entity_id))


if __name__ == '__main__':
    print(MaStateStats)
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

    factor = MaStateStas(codes=codes, start_timestamp='2005-01-01',
                         end_timestamp=now_pd_timestamp(),
                         level=level)
