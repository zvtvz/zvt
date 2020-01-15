# -*- coding: utf-8 -*-
from typing import List

import pandas as pd

from zvdata import IntervalLevel, EntityMixin, Mixin
from zvdata.utils.pd_utils import normal_index_df
from zvt.domain import BlockMoneyFlow
from zvt.factors import ScoreFactor, Union, Scorer, Transformer, Accumulator, Stock
from zvt.factors.algorithm import RankScorer


class BlockMoneyFlowFactor(ScoreFactor):
    def __init__(self, data_schema: Mixin = BlockMoneyFlow, entity_schema: EntityMixin = Stock, provider: str = None,
                 entity_provider: str = None, entity_ids: List[str] = None, exchanges: List[str] = None,
                 codes: List[str] = None, the_timestamp: Union[str, pd.Timestamp] = None,
                 start_timestamp: Union[str, pd.Timestamp] = None, end_timestamp: Union[str, pd.Timestamp] = None,
                 columns: List = None, filters: List = None, order: object = None, limit: int = None,
                 level: Union[str, IntervalLevel] = IntervalLevel.LEVEL_1DAY, category_field: str = 'entity_id',
                 time_field: str = 'timestamp', computing_window: int = None, keep_all_timestamp: bool = False,
                 fill_method: str = 'ffill', effective_number: int = None, transformer: Transformer = None,
                 accumulator: Accumulator = None, persist_factor: bool = False, dry_run: bool = False,
                 scorer: Scorer = RankScorer(ascending=True)) -> None:
        super().__init__(data_schema, entity_schema, provider, entity_provider, entity_ids, exchanges, codes,
                         the_timestamp, start_timestamp, end_timestamp, columns, filters, order, limit, level,
                         category_field, time_field, computing_window, keep_all_timestamp, fill_method,
                         effective_number, transformer, accumulator, persist_factor, dry_run, scorer)

    def do_compute(self):
        self.pipe_df = self.data_df.copy()
        self.pipe_df = self.pipe_df.groupby(level=1).rolling(window=20).mean()
        self.pipe_df = self.pipe_df.reset_index(level=0, drop=True)
        self.pipe_df = self.pipe_df.reset_index()
        self.pipe_df = normal_index_df(self.pipe_df)

        super().do_compute()


__all__ = ['BlockMoneyFlowFactor']

if __name__ == '__main__':
    f1 = BlockMoneyFlowFactor()
