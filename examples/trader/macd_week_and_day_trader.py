# -*- coding: utf-8 -*-
from typing import List, Tuple

from zvt.contract import IntervalLevel
from zvt.factors import TargetSelector, GoldCrossFactor
from zvt.trader.trader import StockTrader


# 依赖数据
# dataschema: Stock1dHfqKdata Stock1wkHfqKdata
# provider: joinquant
class MultipleLevelTrader(StockTrader):
    def init_selectors(
        self, entity_ids, entity_schema, exchanges, codes, start_timestamp, end_timestamp, adjust_type=None
    ):
        # 周线策略
        week_selector = TargetSelector(
            entity_ids=entity_ids,
            entity_schema=entity_schema,
            exchanges=exchanges,
            codes=codes,
            start_timestamp=start_timestamp,
            end_timestamp=end_timestamp,
            long_threshold=0.7,
            level=IntervalLevel.LEVEL_1WEEK,
            provider="joinquant",
        )
        week_gold_cross_factor = GoldCrossFactor(
            entity_ids=entity_ids,
            entity_schema=entity_schema,
            exchanges=exchanges,
            codes=codes,
            start_timestamp=start_timestamp,
            end_timestamp=end_timestamp,
            provider="joinquant",
            level=IntervalLevel.LEVEL_1WEEK,
        )
        week_selector.add_factor(week_gold_cross_factor)

        # 日线策略
        day_selector = TargetSelector(
            entity_ids=entity_ids,
            entity_schema=entity_schema,
            exchanges=exchanges,
            codes=codes,
            start_timestamp=start_timestamp,
            end_timestamp=end_timestamp,
            long_threshold=0.7,
            level=IntervalLevel.LEVEL_1DAY,
            provider="joinquant",
        )
        day_gold_cross_factor = GoldCrossFactor(
            entity_ids=entity_ids,
            entity_schema=entity_schema,
            exchanges=exchanges,
            codes=codes,
            start_timestamp=start_timestamp,
            end_timestamp=end_timestamp,
            provider="joinquant",
            level=IntervalLevel.LEVEL_1DAY,
        )
        day_selector.add_factor(day_gold_cross_factor)

        # 同时使用日线,周线级别
        self.selectors.append(day_selector)
        self.selectors.append(week_selector)

    def on_targets_selected_from_levels(self, timestamp) -> Tuple[List[str], List[str]]:
        # 过滤多级别做 多/空 的标的
        return super().on_targets_selected_from_levels(timestamp)


if __name__ == "__main__":
    trader = MultipleLevelTrader(start_timestamp="2019-01-01", end_timestamp="2020-01-01")
    trader.run()
