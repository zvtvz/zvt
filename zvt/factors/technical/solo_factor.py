# -*- coding: utf-8 -*-
from typing import List, Union

import pandas as pd

from zvt.contract import IntervalLevel, EntityMixin
from zvt.domain import Stock
from zvt.factors.algorithm import IntersectTransformer
from zvt.factors.factor import Transformer, Accumulator
from zvt.factors.technical_factor import TechnicalFactor


class SoloFactor(TechnicalFactor):
    def __init__(self, entity_schema: EntityMixin = Stock, provider: str = None, entity_provider: str = None,
                 entity_ids: List[str] = None, exchanges: List[str] = None, codes: List[str] = None,
                 the_timestamp: Union[str, pd.Timestamp] = None, start_timestamp: Union[str, pd.Timestamp] = None,
                 end_timestamp: Union[str, pd.Timestamp] = None,
                 columns: List = ['id', 'entity_id', 'timestamp', 'open', 'close', 'high', 'low'],
                 filters: List = None, order: object = None, limit: int = None,
                 level: Union[str, IntervalLevel] = IntervalLevel.LEVEL_1DAY, category_field: str = 'entity_id',
                 time_field: str = 'timestamp', computing_window: int = None, keep_all_timestamp: bool = False,
                 fill_method: str = 'ffill', effective_number: int = None,
                 accumulator: Accumulator = None, need_persist: bool = False, dry_run: bool = False,
                 kdata_overlap=3) -> None:
        self.kdata_overlap = kdata_overlap
        transformer: Transformer = IntersectTransformer(kdata_overlap=self.kdata_overlap)

        super().__init__(entity_schema, provider, entity_provider, entity_ids, exchanges, codes, the_timestamp,
                         start_timestamp, end_timestamp, columns, filters, order, limit, level, category_field,
                         time_field, computing_window, keep_all_timestamp, fill_method, effective_number, transformer,
                         accumulator, need_persist, dry_run)

    def do_compute(self):
        super().do_compute()
        # 最近3k线重叠
        filter_se = self.factor_df['overlap'] != (0, 0)

        print(self.factor_df[filter_se])
        self.result_df = filter_se.to_frame(name='score')


if __name__ == '__main__':
    factor = SoloFactor(entity_ids=['stock_sz_000338'], start_timestamp='2015-01-01', end_timestamp='2020-07-01',
                        kdata_overlap=4)
    print(factor.result_df[factor.result_df['score']])
    print(len(factor.result_df))
# the __all__ is generated
__all__ = ['SoloFactor']