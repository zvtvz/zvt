# -*- coding: utf-8 -*-
from typing import List, Union

import pandas as pd

from zvt.contract import IntervalLevel
from zvt.contract.factor import Factor, Transformer, Accumulator
from zvt.domain import Stock, DragonAndTiger
from zvt.trader import StockTrader


class DragonTigerFactor(Factor):
    def __init__(
        self,
        provider: str = "em",
        entity_provider: str = "em",
        entity_ids: List[str] = None,
        exchanges: List[str] = None,
        codes: List[str] = None,
        start_timestamp: Union[str, pd.Timestamp] = None,
        end_timestamp: Union[str, pd.Timestamp] = None,
        columns: List = None,
        filters: List = [DragonAndTiger.dep1 == "机构专用"],
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
    ) -> None:
        super().__init__(
            DragonAndTiger,
            Stock,
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
        )

    def compute_result(self):
        self.factor_df["filter_result"] = True
        super().compute_result()


class MyTrader(StockTrader):
    def init_factors(
        self, entity_ids, entity_schema, exchanges, codes, start_timestamp, end_timestamp, adjust_type=None
    ):
        return [
            DragonTigerFactor(
                entity_ids=entity_ids,
                exchanges=exchanges,
                codes=codes,
                start_timestamp=start_timestamp,
                end_timestamp=end_timestamp,
            )
        ]


if __name__ == "__main__":
    trader = MyTrader(start_timestamp="2020-01-01", end_timestamp="2022-05-01")
    trader.run()
