# -*- coding: utf-8 -*-
from typing import List, Union, Type, Optional

import pandas as pd

from zvt.contract import IntervalLevel, TradableEntity, AdjustType
from zvt.contract.api import get_schema_by_name
from zvt.contract.factor import Accumulator
from zvt.domain import Stock
from zvt.factors.algorithm import live_or_dead
from zvt.factors.technical_factor import TechnicalFactor
from zvt.utils import pd_is_not_null


def get_ma_stats_factor_schema(entity_type: str,
                               level: Union[IntervalLevel, str] = IntervalLevel.LEVEL_1DAY):
    if type(level) == str:
        level = IntervalLevel(level)

    schema_str = '{}{}MaStatsFactor'.format(entity_type.capitalize(), level.value.capitalize())

    return get_schema_by_name(schema_str)


class MaStatsAccumulator(Accumulator):
    def __init__(self, acc_window: int = 250, windows=None, vol_windows=None) -> None:
        super().__init__(acc_window)
        self.windows = windows
        self.vol_windows = vol_windows

    def acc_one(self, entity_id, df: pd.DataFrame, acc_df: pd.DataFrame, state: dict) -> (pd.DataFrame, dict):
        self.logger.info(f'acc_one:{entity_id}')
        if pd_is_not_null(acc_df):
            df = df[df.index > acc_df.index[-1]]
            if pd_is_not_null(df):
                self.logger.info(f'compute from {df.iloc[0]["timestamp"]}')
                acc_df = pd.concat([acc_df, df])
            else:
                self.logger.info('no need to compute')
                return acc_df, state
        else:
            acc_df = df

        for window in self.windows:
            col = 'ma{}'.format(window)
            self.indicators.append(col)

            ma_df = acc_df['close'].rolling(window=window, min_periods=window).mean()
            acc_df[col] = ma_df

        acc_df['live'] = (acc_df['ma5'] > acc_df['ma10']).apply(lambda x: live_or_dead(x))
        acc_df['distance'] = (acc_df['ma5'] - acc_df['ma10']) / acc_df['close']

        live = acc_df['live']
        acc_df['count'] = live * (live.groupby((live != live.shift()).cumsum()).cumcount() + 1)

        acc_df['bulk'] = (live != live.shift()).cumsum()
        area_df = acc_df[['distance', 'bulk']]
        acc_df['area'] = area_df.groupby('bulk').cumsum()

        for vol_window in self.vol_windows:
            col = 'vol_ma{}'.format(vol_window)
            self.indicators.append(col)

            vol_ma_df = acc_df['turnover'].rolling(window=vol_window, min_periods=vol_window).mean()
            acc_df[col] = vol_ma_df

        acc_df = acc_df.set_index('timestamp', drop=False)
        return acc_df, state


class MaStatsFactor(TechnicalFactor):

    def __init__(self, entity_schema: Type[TradableEntity] = Stock, provider: str = None, entity_provider: str = None,
                 entity_ids: List[str] = None, exchanges: List[str] = None, codes: List[str] = None,
                 start_timestamp: Union[str, pd.Timestamp] = None, end_timestamp: Union[str, pd.Timestamp] = None,
                 filters: List = None, order: object = None, limit: int = None,
                 level: Union[str, IntervalLevel] = IntervalLevel.LEVEL_1DAY, category_field: str = 'entity_id',
                 time_field: str = 'timestamp', computing_window: int = None, keep_all_timestamp: bool = False,
                 fill_method: str = 'ffill', effective_number: int = None, need_persist: bool = True,
                 only_compute_factor: bool = False, factor_name: str = None, clear_state: bool = False, only_load_factor: bool = False,
                 adjust_type: Union[AdjustType, str] = None, windows=None, vol_windows=None) -> None:
        if need_persist:
            self.factor_schema = get_ma_stats_factor_schema(entity_type=entity_schema.__name__, level=level)

        if not windows:
            windows = [5, 10, 34, 55, 89, 144, 120, 250]
        self.windows = windows

        if not vol_windows:
            vol_windows = [30]
        self.vol_windows = vol_windows

        columns: List = ['id', 'entity_id', 'timestamp', 'level', 'open', 'close', 'high', 'low', 'turnover']

        accumulator: Accumulator = MaStatsAccumulator(windows=self.windows, vol_windows=self.vol_windows)

        super().__init__(entity_schema, provider, entity_provider, entity_ids, exchanges, codes, start_timestamp,
                         end_timestamp, columns, filters, order, limit, level, category_field,
                         time_field, computing_window, keep_all_timestamp, fill_method, effective_number, None,
                         accumulator, need_persist, only_compute_factor, factor_name, clear_state, only_load_factor, adjust_type)


class TFactor(MaStatsFactor):

    def __init__(self, entity_schema: Type[TradableEntity] = Stock, provider: str = None, entity_provider: str = None,
                 entity_ids: List[str] = None, exchanges: List[str] = None, codes: List[str] = None,
                 start_timestamp: Union[str, pd.Timestamp] = None, end_timestamp: Union[str, pd.Timestamp] = None,
                 filters: List = None, order: object = None, limit: int = None,
                 level: Union[str, IntervalLevel] = IntervalLevel.LEVEL_1DAY,
                 category_field: str = 'entity_id', time_field: str = 'timestamp', computing_window: int = None,
                 keep_all_timestamp: bool = False, fill_method: str = 'ffill', effective_number: int = None,
                 need_persist: bool = True, only_compute_factor: bool = False, factor_name: str = None, clear_state: bool = False,
                 only_load_factor: bool = True, adjust_type: Union[AdjustType, str] = None, windows=None,
                 vol_windows=None) -> None:
        super().__init__(entity_schema, provider, entity_provider, entity_ids, exchanges, codes, start_timestamp,
                         end_timestamp, filters, order, limit, level, category_field, time_field, computing_window,
                         keep_all_timestamp, fill_method, effective_number, need_persist, only_compute_factor, factor_name,
                         clear_state, only_load_factor, adjust_type, windows, vol_windows)

    def drawer_sub_df_list(self) -> Optional[List[pd.DataFrame]]:
        return [self.factor_df[['area']]]

    def drawer_factor_df_list(self) -> Optional[List[pd.DataFrame]]:
        return [self.factor_df[['ma5', 'ma10']]]


if __name__ == '__main__':
    from zvt.factors.ma.domain import *
    codes = ['000338']

    f = TFactor(codes=codes, only_load_factor=False)

    # distribute(f.factor_df[['area']],'area')
    f.draw(show=True)

# the __all__ is generated
__all__ = ['get_ma_stats_factor_schema', 'MaStatsAccumulator', 'MaStatsFactor', 'TFactor']