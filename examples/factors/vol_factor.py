# -*- coding: utf-8 -*-
from typing import List, Union, Type

import pandas as pd

from zvt.contract import AdjustType
from zvt.contract import IntervalLevel, EntityMixin
from zvt.contract.factor import ScoreFactor, Transformer, Accumulator
from zvt.domain import Stock
from zvt.factors import TechnicalFactor
from zvt.factors.algorithm import RankScorer


class VolFactor(TechnicalFactor, ScoreFactor):
    scorer = RankScorer(ascending=True)

    def __init__(self, entity_schema: Type[EntityMixin] = Stock, provider: str = None, entity_provider: str = None,
                 entity_ids: List[str] = None, exchanges: List[str] = None, codes: List[str] = None,
                 the_timestamp: Union[str, pd.Timestamp] = None, start_timestamp: Union[str, pd.Timestamp] = None,
                 end_timestamp: Union[str, pd.Timestamp] = None, filters: List = None,
                 order: object = None, limit: int = None, level: Union[str, IntervalLevel] = IntervalLevel.LEVEL_1DAY,
                 category_field: str = 'entity_id', time_field: str = 'timestamp', computing_window: int = None,
                 keep_all_timestamp: bool = False, fill_method: str = 'ffill', effective_number: int = None,
                 transformer: Transformer = None, accumulator: Accumulator = None, need_persist: bool = False,
                 dry_run: bool = False, factor_name: str = None, clear_state: bool = False,
                 adjust_type: Union[AdjustType, str] = None) -> None:
        super().__init__(entity_schema, provider, entity_provider, entity_ids, exchanges, codes, the_timestamp,
                         start_timestamp, end_timestamp, ['turnover'], filters, order, limit, level, category_field,
                         time_field, computing_window, keep_all_timestamp, fill_method, effective_number, transformer,
                         accumulator, need_persist, dry_run, factor_name, clear_state, adjust_type)

    def pre_compute(self):
        super().pre_compute()
        self.pipe_df = self.pipe_df[['turnover']]
