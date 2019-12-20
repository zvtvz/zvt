# -*- coding: utf-8 -*-
import argparse
from typing import List, Union

import pandas as pd
from zvdata import IntervalLevel
from zvdata.utils.pd_utils import pd_is_not_null
from zvdata.utils.time_utils import now_pd_timestamp

from zvt.api import get_entities, Stock
from zvt.api.common import get_zen_factor_schema
from zvt.factors.factor import Accumulator, Transformer
from zvt.factors.technical_factor import TechnicalFactor


def is_including(s1: pd.Series, s2: pd.Series):
    if (s1['high'] >= s2['high']) and (s1['low'] <= s2['low']):
        return True

    if (s1['high'] <= s2['high']) and (s1['low'] >= s2['low']):
        return True

    return False


def get_current_state(s1: pd.Series, s2: pd.Series, pre_state=0):
    # 上涨
    if (s1['high'] > s2['high']) and (s1['low'] > s2['low']):
        return 1

    # 下跌
    if (s1['high'] < s2['high']) and (s1['low'] < s2['low']):
        return -1

    # 震荡(包含关系)
    return pre_state


class ZenAccumulator(Accumulator):
    def acc(self, input_df, acc_df) -> pd.DataFrame:
        if pd_is_not_null(acc_df):
            input_df = input_df[~input_df['id'].isin(acc_df['id'])]

        input_df = input_df.copy()

        for entity_id, df in input_df.groupby(level=0):
            pre_index = None
            pre_item = None
            current_state = 0
            pre_state = 0

            for index, item in df.iterrows():
                if pre_item is not None:
                    current_state = get_current_state(item, pre_item, current_state)

                input_df.loc[index, 'tmp_bi_state'] = current_state

                if (current_state != 0 and pre_state != 0) and current_state != pre_state:
                    # -1 -> 1
                    if current_state == 1:
                        input_df.loc[pre_index, 'tmp_di'] = True
                    # 1 -> -1
                    if current_state == -1:
                        input_df.loc[pre_index, 'tmp_ding'] = True

                pre_index = index
                pre_item = item
                pre_state = current_state

            print(input_df)
            self.logger.info('finish calculating :{}'.format(entity_id))

        if pd_is_not_null(acc_df):
            if pd_is_not_null(input_df):
                df = input_df[set(acc_df.columns) & set(input_df.columns)]
                acc_df = acc_df.append(df)
                acc_df = acc_df.sort_index(level=[0, 1])
        else:
            acc_df = input_df

        return acc_df


class ZenFactor(TechnicalFactor):

    def __init__(self, entity_ids: List[str] = None, entity_type: str = 'stock', exchanges: List[str] = ['sh', 'sz'],
                 codes: List[str] = None, the_timestamp: Union[str, pd.Timestamp] = None,
                 start_timestamp: Union[str, pd.Timestamp] = None, end_timestamp: Union[str, pd.Timestamp] = None,
                 columns: List = None, filters: List = None, order: object = None, limit: int = None,
                 provider: str = 'joinquant', level: Union[str, IntervalLevel] = IntervalLevel.LEVEL_1DAY,
                 category_field: str = 'entity_id', time_field: str = 'timestamp', computing_window: int = None,
                 keep_all_timestamp: bool = False, fill_method: str = 'ffill', effective_number: int = 10,
                 persist_factor: bool = False, dry_run: bool = True) -> None:
        self.factor_schema = get_zen_factor_schema(entity_type=entity_type, level=level)

        transformer: Transformer = None
        acc = ZenAccumulator()

        super().__init__(entity_ids, entity_type, exchanges, codes, the_timestamp, start_timestamp,
                         end_timestamp, columns, filters, order, limit, provider, level, category_field, time_field,
                         computing_window, keep_all_timestamp, fill_method, effective_number, transformer, acc,
                         persist_factor, dry_run)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--level', help='trading level', default='1d',
                        choices=[item.value for item in IntervalLevel])
    parser.add_argument('--start', help='start code', default='000001')
    parser.add_argument('--end', help='end code', default='000005')

    args = parser.parse_args()

    level = IntervalLevel(args.level)
    start = args.start
    end = args.end

    entities = get_entities(provider='eastmoney', entity_type='stock', columns=[Stock.entity_id, Stock.code],
                            filters=[Stock.code >= start, Stock.code < end])

    codes = entities.index.to_list()

    factor = ZenFactor(codes=codes, start_timestamp='2005-01-01',
                       end_timestamp=now_pd_timestamp(),
                       level=level)
