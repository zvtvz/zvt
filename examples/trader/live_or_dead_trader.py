# -*- coding: utf-8 -*-
from typing import List

from zvt.contract import IntervalLevel
from zvt.factors import TargetSelector, LiveOrDeadFactor, BullFactor
from zvt.trader.trader import StockTrader


class LivePatternFactor(LiveOrDeadFactor):
    pattern = [-5, 1]


class LiveOrDeadTrader(StockTrader):
    def init_selectors(self, entity_ids, entity_schema, exchanges, codes, start_timestamp, end_timestamp):
        # 周线策略
        week_selector = TargetSelector(entity_ids=entity_ids, entity_schema=entity_schema, exchanges=exchanges,
                                       codes=codes, start_timestamp=start_timestamp, end_timestamp=end_timestamp,
                                       provider='joinquant', level=IntervalLevel.LEVEL_1WEEK)
        # 死叉超过5个周期，刚好金叉
        week_factor = LivePatternFactor(entity_ids=entity_ids, entity_schema=entity_schema, exchanges=exchanges,
                                        codes=codes, start_timestamp=start_timestamp, end_timestamp=end_timestamp,
                                        provider='joinquant', level=IntervalLevel.LEVEL_1WEEK)
        week_selector.add_filter_factor(week_factor)

        # 日线策略
        day_selector = TargetSelector(entity_ids=entity_ids, entity_schema=entity_schema, exchanges=exchanges,
                                      codes=codes, start_timestamp=start_timestamp, end_timestamp=end_timestamp,
                                      provider='joinquant', level=IntervalLevel.LEVEL_1DAY)
        # 黄白线在0轴上
        day_factor = BullFactor(entity_ids=entity_ids, entity_schema=entity_schema, exchanges=exchanges,
                                codes=codes, start_timestamp=start_timestamp, end_timestamp=end_timestamp,
                                provider='joinquant', level=IntervalLevel.LEVEL_1DAY)
        day_selector.add_filter_factor(day_factor)

        self.selectors.append(week_selector)
        self.selectors.append(day_selector)

    def filter_selector_short_targets(self, timestamp, selector: TargetSelector, short_targets: List[str]) -> List[str]:
        return short_targets


if __name__ == '__main__':
    trader = LiveOrDeadTrader(start_timestamp='2019-01-01', end_timestamp='2020-01-01')
    trader.run()
