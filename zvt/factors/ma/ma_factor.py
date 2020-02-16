# -*- coding: utf-8 -*-
import argparse
from typing import List, Union

import pandas as pd

from zvdata import IntervalLevel, EntityMixin
from zvdata.utils.time_utils import now_pd_timestamp
from zvt.api import get_entities, Stock
from zvt.api.common import get_ma_factor_schema
from zvt.factors import Accumulator
from zvt.factors.algorithm import MaTransformer, MaAndVolumeTransformer
from zvt.factors.factor import Transformer
from zvt.factors.technical_factor import TechnicalFactor


class MaFactor(TechnicalFactor):

    def __init__(self, entity_schema: EntityMixin = Stock, provider: str = None, entity_provider: str = None,
                 entity_ids: List[str] = None, exchanges: List[str] = None, codes: List[str] = None,
                 the_timestamp: Union[str, pd.Timestamp] = None, start_timestamp: Union[str, pd.Timestamp] = None,
                 end_timestamp: Union[str, pd.Timestamp] = None,
                 columns: List = ['id', 'entity_id', 'timestamp', 'level', 'open', 'close', 'high', 'low'],
                 filters: List = None, order: object = None, limit: int = None,
                 level: Union[str, IntervalLevel] = IntervalLevel.LEVEL_1DAY, category_field: str = 'entity_id',
                 time_field: str = 'timestamp', computing_window: int = None, keep_all_timestamp: bool = False,
                 fill_method: str = 'ffill', effective_number: int = None,
                 accumulator: Accumulator = None, persist_factor: bool = False, dry_run: bool = False,
                 windows=[5, 10, 34, 55, 89, 144, 120, 250]) -> None:
        self.factor_schema = get_ma_factor_schema(entity_type=entity_schema.__name__, level=level)
        self.windows = windows

        transformer: Transformer = MaTransformer(windows=windows)

        super().__init__(entity_schema, provider, entity_provider, entity_ids, exchanges, codes, the_timestamp,
                         start_timestamp, end_timestamp, columns, filters, order, limit, level, category_field,
                         time_field, computing_window, keep_all_timestamp, fill_method, effective_number, transformer,
                         accumulator, persist_factor, dry_run)


class CrossMaFactor(MaFactor):
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


class VolumeUpMa250Factor(TechnicalFactor):
    def __init__(self, entity_schema: EntityMixin = Stock, provider: str = None, entity_provider: str = None,
                 entity_ids: List[str] = None, exchanges: List[str] = None, codes: List[str] = None,
                 the_timestamp: Union[str, pd.Timestamp] = None, start_timestamp: Union[str, pd.Timestamp] = None,
                 end_timestamp: Union[str, pd.Timestamp] = None,
                 columns: List = ['id', 'entity_id', 'timestamp', 'level', 'open', 'close', 'high', 'low', 'volume'],
                 filters: List = None, order: object = None, limit: int = None,
                 level: Union[str, IntervalLevel] = IntervalLevel.LEVEL_1DAY, category_field: str = 'entity_id',
                 time_field: str = 'timestamp', computing_window: int = None, keep_all_timestamp: bool = False,
                 fill_method: str = 'ffill', effective_number: int = None,
                 accumulator: Accumulator = None, persist_factor: bool = False, dry_run: bool = False,
                 windows=[250], vol_windows=[30]) -> None:
        self.windows = windows
        self.vol_windows = vol_windows

        transformer: Transformer = MaAndVolumeTransformer(windows=windows, vol_windows=vol_windows)

        super().__init__(entity_schema, provider, entity_provider, entity_ids, exchanges, codes, the_timestamp,
                         start_timestamp, end_timestamp, columns, filters, order, limit, level, category_field,
                         time_field, computing_window, keep_all_timestamp, fill_method, effective_number, transformer,
                         accumulator, persist_factor, dry_run)

    def do_compute(self):
        super().do_compute()

        # 价格刚上均线
        cols = [f'ma{window}' for window in self.windows]
        filter_se = (self.factor_df['close'] > self.factor_df[cols[0]]) & (
                self.factor_df['close'] < 1.1 * self.factor_df[cols[0]])
        for col in cols[1:]:
            filter_se = filter_se & (self.factor_df['close'] > self.factor_df[col])

        # 放量
        vol_cols = [f'vol_ma{window}' for window in self.vol_windows]
        filter_se = filter_se & (self.factor_df['volume'] > 2 * self.factor_df[vol_cols[0]])
        for col in vol_cols[1:]:
            filter_se = filter_se & (self.factor_df['volume'] > 2 * self.factor_df[col])

        print(self.factor_df[filter_se])
        self.result_df = filter_se.to_frame(name='score')


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
