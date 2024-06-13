# -*- coding: utf-8 -*-

from typing import Type, List, Union

import pandas as pd

from zvt.contract import AdjustType, TradableEntity, IntervalLevel
from zvt.contract.factor import Transformer, Accumulator
from zvt.domain import Stock
from zvt.factors.macd.macd_factor import MacdFactor
from zvt.factors.transformers import CrossMaTransformer


class BullAndUpFactor(MacdFactor):
    def __init__(
        self,
        entity_schema: Type[TradableEntity] = Stock,
        provider: str = None,
        entity_provider: str = None,
        entity_ids: List[str] = None,
        exchanges: List[str] = None,
        codes: List[str] = None,
        start_timestamp: Union[str, pd.Timestamp] = None,
        end_timestamp: Union[str, pd.Timestamp] = None,
        columns: List = None,
        filters: List = None,
        order: object = None,
        limit: int = None,
        level: Union[str, IntervalLevel] = IntervalLevel.LEVEL_1DAY,
        category_field: str = "entity_id",
        time_field: str = "timestamp",
        keep_window: int = None,
        keep_all_timestamp: bool = False,
        fill_method: str = "ffill",
        effective_number: int = None,
        transformer: Transformer = None,
        accumulator: Accumulator = None,
        need_persist: bool = False,
        only_compute_factor: bool = False,
        factor_name: str = None,
        clear_state: bool = False,
        only_load_factor: bool = False,
        adjust_type: Union[AdjustType, str] = None,
        turnover_threshold=400000000,
        turnover_rate_threshold=0.02,
    ) -> None:
        self.turnover_threshold = turnover_threshold
        self.turnover_rate_threshold = turnover_rate_threshold

        super().__init__(
            entity_schema,
            provider,
            entity_provider,
            entity_ids,
            exchanges,
            codes,
            start_timestamp,
            end_timestamp,
            columns,
            filters,
            order,
            limit,
            level,
            category_field,
            time_field,
            keep_window,
            keep_all_timestamp,
            fill_method,
            effective_number,
            transformer,
            accumulator,
            need_persist,
            only_compute_factor,
            factor_name,
            clear_state,
            only_load_factor,
            adjust_type,
        )

    def compute_result(self):
        super().compute_result()
        t = CrossMaTransformer(windows=[5, 120, 250])
        self.factor_df = t.transform(self.factor_df)
        s = (self.factor_df["turnover"] > self.turnover_threshold) & (
            self.factor_df["turnover_rate"] > self.turnover_rate_threshold
        )
        self.result_df = (self.factor_df["filter_result"] & self.factor_df["bull"] & s).to_frame(name="filter_result")
