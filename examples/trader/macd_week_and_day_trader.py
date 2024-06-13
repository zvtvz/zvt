# -*- coding: utf-8 -*-
from typing import List, Tuple

from zvt.contract import IntervalLevel
from zvt.factors.macd.macd_factor import GoldCrossFactor
from zvt.trader.trader import StockTrader


# 依赖数据
# dataschema: Stock1dHfqKdata Stock1wkHfqKdata
# provider: joinquant
class MultipleLevelTrader(StockTrader):
    def init_factors(
        self, entity_ids, entity_schema, exchanges, codes, start_timestamp, end_timestamp, adjust_type=None
    ):
        # 同时使用周线和日线策略
        return [
            GoldCrossFactor(
                entity_ids=entity_ids,
                entity_schema=entity_schema,
                exchanges=exchanges,
                codes=codes,
                start_timestamp=start_timestamp,
                end_timestamp=end_timestamp,
                provider="joinquant",
                level=IntervalLevel.LEVEL_1WEEK,
            ),
            GoldCrossFactor(
                entity_ids=entity_ids,
                entity_schema=entity_schema,
                exchanges=exchanges,
                codes=codes,
                start_timestamp=start_timestamp,
                end_timestamp=end_timestamp,
                provider="joinquant",
                level=IntervalLevel.LEVEL_1DAY,
            ),
        ]

    def on_targets_selected_from_levels(self, timestamp) -> Tuple[List[str], List[str]]:
        # 过滤多级别做 多/空 的标的
        return super().on_targets_selected_from_levels(timestamp)


if __name__ == "__main__":
    trader = MultipleLevelTrader(start_timestamp="2019-01-01", end_timestamp="2020-01-01")
    trader.run()
