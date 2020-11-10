from typing import List, Union

import numpy as np
import pandas as pd

from zvt.api.quote import get_kdata_schema
from zvt.contract import IntervalLevel, EntityMixin, AdjustType
from zvt.domain import Stock
from zvt.factors.algorithm import MacdTransformer, consecutive_count
from zvt.factors.factor import Factor, Transformer, Accumulator


class TechnicalFactor(Factor):
    def __init__(self,
                 entity_schema: EntityMixin = Stock,
                 provider: str = None,
                 entity_provider: str = None,
                 entity_ids: List[str] = None,
                 exchanges: List[str] = None,
                 codes: List[str] = None,
                 the_timestamp: Union[str, pd.Timestamp] = None,
                 start_timestamp: Union[str, pd.Timestamp] = None,
                 end_timestamp: Union[str, pd.Timestamp] = None,
                 columns: List = None,
                 filters: List = None,
                 order: object = None,
                 limit: int = None,
                 level: Union[str, IntervalLevel] = IntervalLevel.LEVEL_1DAY,
                 category_field: str = 'entity_id',
                 time_field: str = 'timestamp',
                 computing_window: int = None,
                 keep_all_timestamp: bool = False,
                 fill_method: str = 'ffill',
                 effective_number: int = None,
                 transformer: Transformer = MacdTransformer(),
                 accumulator: Accumulator = None,
                 need_persist: bool = False,
                 dry_run: bool = False,
                 adjust_type: Union[AdjustType, str] = None) -> None:
        if columns is None:
            columns = ['id', 'entity_id', 'timestamp', 'level', 'open', 'close', 'high', 'low']
        self.adjust_type = adjust_type
        self.data_schema = get_kdata_schema(entity_schema.__name__, level=level, adjust_type=adjust_type)

        if transformer:
            self.indicator_cols = transformer.indicators

        super().__init__(self.data_schema, entity_schema, provider, entity_provider, entity_ids, exchanges, codes,
                         the_timestamp, start_timestamp, end_timestamp, columns, filters, order, limit, level,
                         category_field, time_field, computing_window, keep_all_timestamp, fill_method,
                         effective_number, transformer, accumulator, need_persist, dry_run)

    def __json__(self):
        result = super().__json__()
        result['indicator_cols'] = self.indicator_cols
        return result

    for_json = __json__  # supported by simplejson


class BullFactor(TechnicalFactor):
    def do_compute(self):
        super().do_compute()
        s = (self.factor_df['diff'] > 0) & (self.factor_df['dea'] > 0)
        self.result_df = s.to_frame(name='score')


class KeepBullFactor(BullFactor):
    def __init__(self, entity_schema: EntityMixin = Stock, provider: str = None, entity_provider: str = None,
                 entity_ids: List[str] = None, exchanges: List[str] = None, codes: List[str] = None,
                 the_timestamp: Union[str, pd.Timestamp] = None, start_timestamp: Union[str, pd.Timestamp] = None,
                 end_timestamp: Union[str, pd.Timestamp] = None,
                 columns=None,
                 filters: List = None, order: object = None, limit: int = None,
                 level: Union[str, IntervalLevel] = IntervalLevel.LEVEL_1DAY, category_field: str = 'entity_id',
                 time_field: str = 'timestamp', computing_window: int = None, keep_all_timestamp: bool = False,
                 fill_method: str = 'ffill', effective_number: int = None, transformer: Transformer = MacdTransformer(),
                 accumulator: Accumulator = None, need_persist: bool = False, dry_run: bool = False,
                 adjust_type: Union[AdjustType, str] = None, keep_window=20) -> None:
        self.keep_window = keep_window
        super().__init__(entity_schema, provider, entity_provider, entity_ids, exchanges, codes, the_timestamp,
                         start_timestamp, end_timestamp, columns, filters, order, limit, level, category_field,
                         time_field, computing_window, keep_all_timestamp, fill_method, effective_number, transformer,
                         accumulator, need_persist, dry_run, adjust_type)

    def do_compute(self):
        super().do_compute()
        df = self.result_df['score'].groupby(level=0).rolling(window=self.keep_window,
                                                              min_periods=self.keep_window).apply(
            lambda x: np.logical_and.reduce(x))
        df = df.reset_index(level=0, drop=True)
        self.result_df['score'] = df


# 金叉 死叉 持续时间 切换点
class LiveOrDeadFactor(TechnicalFactor):
    pattern = [-5, 1]

    def do_compute(self):
        super().do_compute()
        # 白线在黄线之上
        s = self.factor_df['diff'] > self.factor_df['dea']
        # live=True 白线>黄线
        # live=False 白线<黄线
        self.factor_df['live'] = s.to_frame()
        consecutive_count(self.factor_df, 'live', pattern=self.pattern)
        self.result_df = self.factor_df[['score']]


class GoldCrossFactor(LiveOrDeadFactor):
    def do_compute(self):
        super().do_compute()
        s = self.factor_df['live'] == 1
        self.result_df = s.to_frame(name='score')


if __name__ == '__main__':
    factor = TechnicalFactor(codes=['000338', '000778'],
                             start_timestamp='2019-01-01',
                             end_timestamp='2019-06-10',
                             transformer=MacdTransformer(normal=True))

    print(factor.factor_df.tail())

    factor.move_on(to_timestamp='2019-06-17')
    diff = factor.factor_df['diff']
    dea = factor.factor_df['dea']
    macd = factor.factor_df['macd']

    print(factor.factor_df.loc[('stock_sz_000338',)])
    print(factor.factor_df.loc[('stock_sz_000778',)])
# the __all__ is generated
__all__ = ['TechnicalFactor', 'BullFactor', 'KeepBullFactor', 'LiveOrDeadFactor', 'GoldCrossFactor']