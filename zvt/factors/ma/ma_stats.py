# -*- coding: utf-8 -*-
import argparse
from typing import List, Union

import pandas as pd

from zvdata import IntervalLevel, EntityMixin
from zvdata.utils.pd_utils import pd_is_not_null
from zvdata.utils.time_utils import now_pd_timestamp
from zvt.api import get_entities, Stock
from zvt.api.common import get_ma_state_stats_schema
from zvt.factors.algorithm import MaTransformer
from zvt.factors.factor import Accumulator, Transformer
from zvt.factors.technical_factor import TechnicalFactor


# 均线状态统计
class MaAccumulator(Accumulator):

    def __init__(self, short_window, long_window) -> None:
        self.short_window = short_window
        self.long_window = long_window

        self.current_col = 'current_count'
        self.total_col = 'total_count'
        self.acc_window = 1

    def acc(self, input_df, acc_df) -> pd.DataFrame:
        short_ma_col = 'ma{}'.format(self.short_window)
        long_ma_col = 'ma{}'.format(self.long_window)

        input_df['score'] = input_df[short_ma_col] > input_df[long_ma_col]

        # 过滤掉已经计算的时间
        if pd_is_not_null(acc_df):
            dfs = []
            for entity_id, df in input_df.groupby(level=0):
                if entity_id in acc_df.index.levels[0]:
                    df = df[df.timestamp > acc_df.loc[(entity_id,)].index[-1]]
                dfs.append(df)

            input_df = pd.concat(dfs, sort=False)

        for entity_id, df in input_df.groupby(level=0):
            count = 0
            current_state = None
            pre_index = None
            check_acc = False
            for index, item in df['score'].iteritems():
                # ５日线在１０日线之上
                if item:
                    state = 'up'
                # ５日线在１０日线之下
                elif not pd.isna(df[short_ma_col][index]) and not pd.isna(df[long_ma_col][index]):
                    state = 'down'
                else:
                    continue

                # 计算维持状态（'up','down'）的 次数
                if current_state == state:
                    if count > 0:
                        count = count + 1
                    else:
                        count = count - 1
                else:
                    # 状态切换，设置前一状态的总和
                    if count != 0:
                        input_df.loc[pre_index, self.total_col] = count
                    current_state = state

                    if current_state == 'up':
                        count = 1
                    else:
                        count = -1

                    # 增量计算，需要累加之前的结果
                    if pd_is_not_null(acc_df) and not check_acc:
                        if entity_id in acc_df.index.levels[0]:
                            acc_col_current = acc_df.loc[(entity_id,)].iloc[-1][self.current_col]
                            if not pd.isna(acc_col_current):
                                # up
                                if acc_col_current > 0 and (current_state == 'up'):
                                    count = acc_col_current + 1
                                # down
                                elif acc_col_current < 0 and (current_state == 'down'):
                                    count = acc_col_current - 1
                                # state has changed
                                else:
                                    pre_timestamp = acc_df.loc[(entity_id,), 'timestamp'][-1]
                                    acc_df.loc[(entity_id, pre_timestamp), self.total_col] = acc_col_current
                        check_acc = True

                # 设置目前状态
                input_df.loc[index, self.current_col] = count

                pre_index = index

            self.logger.info('finish calculating :{}'.format(entity_id))

        if pd_is_not_null(acc_df):
            if pd_is_not_null(input_df):
                df = input_df[set(acc_df.columns) & set(input_df.columns)]
                acc_df = acc_df.append(df, sort=False)
                acc_df = acc_df.sort_index(level=[0, 1])
        else:
            acc_df = input_df

        return acc_df


class MaStateStas(TechnicalFactor):

    def __init__(self, entity_schema: EntityMixin = Stock, provider: str = None, entity_provider: str = None,
                 entity_ids: List[str] = None, exchanges: List[str] = None, codes: List[str] = None,
                 the_timestamp: Union[str, pd.Timestamp] = None, start_timestamp: Union[str, pd.Timestamp] = None,
                 end_timestamp: Union[str, pd.Timestamp] = None,
                 columns: List = ['id', 'entity_id', 'timestamp', 'level', 'open', 'close', 'high', 'low'],
                 filters: List = None, order: object = None, limit: int = None,
                 level: Union[str, IntervalLevel] = IntervalLevel.LEVEL_1DAY, category_field: str = 'entity_id',
                 time_field: str = 'timestamp', computing_window: int = 10, keep_all_timestamp: bool = False,
                 fill_method: str = 'ffill', effective_number: int = None,
                 persist_factor: bool = True, dry_run: bool = True,
                 # added fields
                 short_window: int = 5,
                 long_window: int = 10) -> None:
        self.factor_schema = get_ma_state_stats_schema(entity_type=entity_schema.__name__, level=level)
        self.short_window = short_window
        self.long_window = long_window

        transformer: Transformer = MaTransformer(windows=[short_window, long_window])
        accumulator = MaAccumulator(short_window=short_window, long_window=long_window)

        super().__init__(entity_schema, provider, entity_provider, entity_ids, exchanges, codes, the_timestamp,
                         start_timestamp, end_timestamp, columns, filters, order, limit, level, category_field,
                         time_field, computing_window, keep_all_timestamp, fill_method, effective_number, transformer,
                         accumulator, persist_factor, dry_run)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--level', help='trading level', default='1d',
                        choices=[item.value for item in IntervalLevel])
    parser.add_argument('--start', help='start code', default='000338')
    parser.add_argument('--end', help='end code', default='000339')

    args = parser.parse_args()

    level = IntervalLevel(args.level)
    start = args.start
    end = args.end

    entities = get_entities(provider='joinquant', entity_type='stock', columns=[Stock.entity_id, Stock.code],
                            filters=[Stock.code >= start, Stock.code < end])

    codes = entities.index.to_list()

    factor = MaStateStas(codes=codes, start_timestamp='2005-01-01',
                         end_timestamp=now_pd_timestamp(),
                         level=level)
