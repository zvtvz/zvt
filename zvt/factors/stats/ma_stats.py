# -*- coding: utf-8 -*-
import argparse
from typing import List, Union

import pandas as pd
from sqlalchemy import Column, String, Float, Integer
from sqlalchemy.ext.declarative import declarative_base

from zvdata import IntervalLevel, Mixin
from zvdata.scorer import Transformer, Accumulator
from zvdata.utils.pd_utils import df_is_not_null
from zvdata.utils.time_utils import now_pd_timestamp
from zvt import register_schema
from zvt.api import get_entities, Stock
from zvt.factors.technical_factor import TechnicalFactor, MaTransformer
# 均线状态统计
from zvt.settings import SAMPLE_STOCK_CODES

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


class MaAccumulator(Accumulator):

    def __init__(self, short_window, long_window) -> None:
        self.short_window = short_window
        self.long_window = long_window

    def acc(self, input_df, acc_df) -> pd.DataFrame:
        short_ma_col = 'ma{}'.format(self.short_window)
        long_ma_col = 'ma{}'.format(self.long_window)

        input_df['score'] = input_df[short_ma_col] > input_df[long_ma_col]

        if df_is_not_null(acc_df):
            input_df = input_df[~input_df['id'].isin(acc_df['id'])]

        input_df = input_df.copy()

        for entity_id, df in input_df.groupby(level=0):
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
                    area += abs(input_df.loc[index, long_ma_col] - input_df.loc[index, short_ma_col])
                else:
                    # change state,set pre state total count
                    if count > 0:
                        input_df.loc[pre_index, pre_col_total] = count
                    current_state = state

                    count = 1
                    # 增量计算，需要累加之前的结果
                    if df_is_not_null(acc_df):
                        if entity_id in acc_df.index.levels[0]:
                            acc_col_current = acc_df.loc[(entity_id,)].iloc[-1][col_current]
                            if not pd.isna(acc_col_current):
                                count = acc_col_current + 1

                    area = abs(input_df.loc[index, long_ma_col] - input_df.loc[index, short_ma_col])

                input_df.loc[index, col_current] = count
                input_df.loc[index, col_area] = area

                pre_index = index
                pre_col_total = col_total

                # 短期均线　长期均线的距离
                # input_df.loc[index, 'distance'] = abs(input_df.loc[index, short_ma_col] - input_df.loc[
                #     index, long_ma_col]) / input_df.loc[index, long_ma_col]

            print('finish calculating :{}'.format(entity_id))

        if df_is_not_null(acc_df):
            if df_is_not_null(input_df):
                df = input_df[set(acc_df.columns) & set(input_df.columns)]
                acc_df = acc_df.append(df)
                acc_df = acc_df.sort_index(level=[0, 1])
        else:
            acc_df = input_df

        return acc_df


class MaStateStas(TechnicalFactor):
    factor_schema = MaStateStats

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
                 level: Union[str, IntervalLevel] = IntervalLevel.LEVEL_1DAY,
                 category_field: str = 'entity_id',
                 time_field: str = 'timestamp',
                 auto_load: bool = True,
                 valid_window: int = 10,
                 keep_all_timestamp: bool = False,
                 fill_method: str = 'ffill',
                 effective_number: int = 10,
                 need_persist: bool = True,
                 dry_run: bool = True,
                 # added fields
                 short_window: int = 5,
                 long_window: int = 10) -> None:
        self.short_window = short_window
        self.long_window = long_window

        transformers: List[Transformer] = [MaTransformer(windows=[short_window, long_window])]
        acc = MaAccumulator(short_window=short_window, long_window=long_window)

        super().__init__(entity_ids, entity_type, exchanges, codes, the_timestamp, start_timestamp,
                         end_timestamp, columns, filters, order, limit, provider, level, category_field, time_field,
                         auto_load, valid_window, keep_all_timestamp, fill_method, effective_number, transformers, acc,
                         need_persist, dry_run)


if __name__ == '__main__':
    print('start')
    parser = argparse.ArgumentParser()
    parser.add_argument('--level', help='trading level', default='1d',
                        choices=[item.value for item in IntervalLevel])
    parser.add_argument('--start', help='start code', default='000001')
    parser.add_argument('--end', help='end code', default='000003')

    args = parser.parse_args()

    level = IntervalLevel(args.level)
    start = args.start
    end = args.end

    entities = get_entities(provider='eastmoney', entity_type='stock', columns=[Stock.entity_id, Stock.code],
                            filters=[Stock.code >= start, Stock.code < end])

    codes = entities.index.to_list()

    factor = MaStateStas(codes=SAMPLE_STOCK_CODES, start_timestamp='2005-01-01',
                         end_timestamp=now_pd_timestamp(),
                         level=level)
