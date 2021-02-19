# -*- coding: utf-8 -*-
import argparse
from typing import List, Union, Type, Optional

import pandas as pd

from zvt.contract import IntervalLevel, EntityMixin, AdjustType
from zvt.contract.api import get_entities, get_schema_by_name
from zvt.contract.factor import Accumulator
from zvt.contract.factor import Transformer
from zvt.domain import Stock
from zvt.factors.algorithm import MaTransformer, MaAndVolumeTransformer
from zvt.factors.technical_factor import TechnicalFactor
from zvt.utils.time_utils import now_pd_timestamp


def get_ma_factor_schema(entity_type: str,
                         level: Union[IntervalLevel, str] = IntervalLevel.LEVEL_1DAY):
    if type(level) == str:
        level = IntervalLevel(level)

    schema_str = '{}{}MaFactor'.format(entity_type.capitalize(), level.value.capitalize())

    return get_schema_by_name(schema_str)


class MaFactor(TechnicalFactor):
    def __init__(self, entity_schema: Type[EntityMixin] = Stock, provider: str = None, entity_provider: str = None,
                 entity_ids: List[str] = None, exchanges: List[str] = None, codes: List[str] = None,
                 the_timestamp: Union[str, pd.Timestamp] = None, start_timestamp: Union[str, pd.Timestamp] = None,
                 end_timestamp: Union[str, pd.Timestamp] = None, columns: List = None, filters: List = None,
                 order: object = None, limit: int = None, level: Union[str, IntervalLevel] = IntervalLevel.LEVEL_1DAY,
                 category_field: str = 'entity_id', time_field: str = 'timestamp', computing_window: int = None,
                 keep_all_timestamp: bool = False, fill_method: str = 'ffill', effective_number: int = None,
                 need_persist: bool = False,
                 dry_run: bool = False, factor_name: str = None, clear_state: bool = False, not_load_data: bool = False,
                 adjust_type: Union[AdjustType, str] = None, windows=None) -> None:
        if need_persist:
            self.factor_schema = get_ma_factor_schema(entity_type=entity_schema.__name__, level=level)

        if not windows:
            windows = [5, 10, 34, 55, 89, 144, 120, 250]
        self.windows = windows
        transformer: Transformer = MaTransformer(windows=windows)

        super().__init__(entity_schema, provider, entity_provider, entity_ids, exchanges, codes, the_timestamp,
                         start_timestamp, end_timestamp, columns, filters, order, limit, level, category_field,
                         time_field, computing_window, keep_all_timestamp, fill_method, effective_number, transformer,
                         None, need_persist, dry_run, factor_name, clear_state, not_load_data, adjust_type)

    def drawer_factor_df_list(self) -> Optional[List[pd.DataFrame]]:
        return [self.factor_df[self.transformer.indicators]]


class CrossMaFactor(MaFactor):
    def compute_result(self):
        super().compute_result()
        cols = [f'ma{window}' for window in self.windows]
        s = self.factor_df[cols[0]] > self.factor_df[cols[1]]
        current_col = cols[1]
        for col in cols[2:]:
            s = s & (self.factor_df[current_col] > self.factor_df[col])
            current_col = col

        print(self.factor_df[s])
        self.result_df = s.to_frame(name='score')


class VolumeUpMaFactor(TechnicalFactor):

    def __init__(self, entity_schema: Type[EntityMixin] = Stock, provider: str = None, entity_provider: str = None,
                 entity_ids: List[str] = None, exchanges: List[str] = None, codes: List[str] = None,
                 the_timestamp: Union[str, pd.Timestamp] = None, start_timestamp: Union[str, pd.Timestamp] = None,
                 end_timestamp: Union[str, pd.Timestamp] = None, filters: List = None,
                 order: object = None, limit: int = None, level: Union[str, IntervalLevel] = IntervalLevel.LEVEL_1DAY,
                 category_field: str = 'entity_id', time_field: str = 'timestamp', computing_window: int = None,
                 keep_all_timestamp: bool = False, fill_method: str = 'ffill', effective_number: int = None,
                 accumulator: Accumulator = None, need_persist: bool = False,
                 dry_run: bool = False, factor_name: str = None, clear_state: bool = False, not_load_data: bool = False,
                 adjust_type: Union[AdjustType, str] = None, windows=None, vol_windows=None) -> None:
        if not windows:
            windows = [250]
        if not vol_windows:
            vol_windows = [30]

        self.windows = windows
        self.vol_windows = vol_windows

        columns: List = ['id', 'entity_id', 'timestamp', 'level', 'open', 'close', 'high', 'low', 'volume',
                         'turnover']

        transformer: Transformer = MaAndVolumeTransformer(windows=windows, vol_windows=vol_windows)

        super().__init__(entity_schema, provider, entity_provider, entity_ids, exchanges, codes, the_timestamp,
                         start_timestamp, end_timestamp, columns, filters, order, limit, level, category_field,
                         time_field, computing_window, keep_all_timestamp, fill_method, effective_number, transformer,
                         accumulator, need_persist, dry_run, factor_name, clear_state, not_load_data, adjust_type)

    def compute_result(self):
        super().compute_result()

        # 价格刚上均线
        cols = [f'ma{window}' for window in self.windows]
        filter_se = (self.factor_df['close'] > self.factor_df[cols[0]]) & (
                self.factor_df['close'] < 1.1 * self.factor_df[cols[0]])
        for col in cols[1:]:
            filter_se = filter_se & (self.factor_df['close'] > self.factor_df[col])

        # 放量
        if self.vol_windows:
            vol_cols = [f'vol_ma{window}' for window in self.vol_windows]
            filter_se = filter_se & (self.factor_df['volume'] > 2 * self.factor_df[vol_cols[0]])
            for col in vol_cols[1:]:
                filter_se = filter_se & (self.factor_df['volume'] > 2 * self.factor_df[col])

        # 成交额大于1亿️
        filter_se = filter_se & (self.factor_df['turnover'] > 100000000)

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

    factor = VolumeUpMaFactor(entity_ids=['stock_sz_000338'], start_timestamp='2020-01-01',
                              end_timestamp=now_pd_timestamp(), need_persist=False,
                              level=level)
    print(factor.result_df)
# the __all__ is generated
__all__ = ['get_ma_factor_schema', 'MaFactor', 'CrossMaFactor', 'VolumeUpMaFactor']
