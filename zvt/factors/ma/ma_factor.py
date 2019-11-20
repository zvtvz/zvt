# -*- coding: utf-8 -*-
import argparse
from typing import List, Union

import pandas as pd

from zvdata import IntervalLevel
from zvdata.utils.time_utils import now_pd_timestamp
from zvt.api import get_entities, Stock
from zvt.api.common import get_ma_factor_schema
from zvt.factors.algorithm import MaTransformer
from zvt.factors.factor import Transformer
from zvt.factors.technical_factor import TechnicalFactor


class MaFactor(TechnicalFactor):
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
                 computing_window: int = 250,
                 keep_all_timestamp: bool = False,
                 fill_method: str = 'ffill',
                 effective_number: int = 10,
                 persist_factor: bool = True,
                 dry_run: bool = True,
                 windows=[5, 10, 34, 55, 89, 144, 120, 250]) -> None:
        self.factor_schema = get_ma_factor_schema(entity_type=entity_type, level=level)
        self.windows = windows

        transformer: Transformer = MaTransformer(windows=windows)

        super().__init__(entity_ids, entity_type, exchanges, codes, the_timestamp, start_timestamp,
                         end_timestamp, columns, filters, order, limit, provider, level, category_field, time_field,
                         computing_window, keep_all_timestamp, fill_method, effective_number, transformer, None,
                         persist_factor, dry_run)


class CrossMaFactor(MaFactor):
    def __init__(self, entity_ids: List[str] = None, entity_type: str = 'stock', exchanges: List[str] = ['sh', 'sz'],
                 codes: List[str] = None, the_timestamp: Union[str, pd.Timestamp] = None,
                 start_timestamp: Union[str, pd.Timestamp] = None, end_timestamp: Union[str, pd.Timestamp] = None,
                 columns: List = None, filters: List = None, order: object = None, limit: int = None,
                 provider: str = 'joinquant', level: Union[str, IntervalLevel] = IntervalLevel.LEVEL_1DAY,
                 category_field: str = 'entity_id', time_field: str = 'timestamp', computing_window: int = 250,
                 keep_all_timestamp: bool = False, fill_method: str = 'ffill', effective_number: int = 10,
                 persist_factor: bool = True, dry_run=False, windows=[5, 10, 34, 55, 89, 144, 120, 250]) -> None:
        super().__init__(entity_ids, entity_type, exchanges, codes, the_timestamp, start_timestamp, end_timestamp,
                         columns, filters, order, limit, provider, level, category_field, time_field, computing_window,
                         keep_all_timestamp, fill_method, effective_number, persist_factor, dry_run,
                         windows=windows)

    def do_compute(self):
        super().do_compute()
        cols = [f'ma{window}' for window in self.windows]
        s = self.factor_df[cols[0]] > self.factor_df[cols[1]]
        current_col = cols[1]
        for col in cols[2:]:
            s = s & (self.factor_df[current_col] > self.factor_df[col])
            current_col = col

        print(self.factor_df[s])
        self.result_df = s.to_frame(name='score')


if __name__ == '__main__':
    print('start')
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

    factor = CrossMaFactor(entity_ids=['000001'], start_timestamp='2005-01-01',
                           end_timestamp=now_pd_timestamp(), persist_factor=False,
                           level=level)
