# -*- coding: utf-8 -*-
import datetime
from typing import List

from zvt.contract import IntervalLevel
from zvt.domain import FinanceFactor
from zvt.factors import TargetSelector, KeepBullFactor
from zvt.trader.trader import StockTrader
from zvt.utils.pd_utils import pd_is_not_null


class MultipleLevelBullTrader(StockTrader):
    def init_selectors(self, entity_ids, entity_schema, exchanges, codes, start_timestamp, end_timestamp):
        # 周线策略
        week_bull_selector = TargetSelector(entity_ids=entity_ids, entity_schema=entity_schema, exchanges=exchanges,
                                            codes=codes, start_timestamp=start_timestamp, end_timestamp=end_timestamp,
                                            provider='joinquant', level=IntervalLevel.LEVEL_1WEEK)
        # 最近20周黄白线在0轴上
        week_bull_factor = KeepBullFactor(entity_ids=entity_ids, entity_schema=entity_schema, exchanges=exchanges,
                                          codes=codes, start_timestamp=start_timestamp, end_timestamp=end_timestamp,
                                          provider='joinquant', level=IntervalLevel.LEVEL_1WEEK, keep_window=20)
        week_bull_selector.add_filter_factor(week_bull_factor)

        # 日线策略
        day_bull_selector = TargetSelector(entity_ids=entity_ids, entity_schema=entity_schema, exchanges=exchanges,
                                           codes=codes, start_timestamp=start_timestamp, end_timestamp=end_timestamp,
                                           provider='joinquant', level=IntervalLevel.LEVEL_1DAY)
        day_bull_factor = KeepBullFactor(entity_ids=entity_ids, entity_schema=entity_schema, exchanges=exchanges,
                                         codes=codes, start_timestamp=start_timestamp, end_timestamp=end_timestamp,
                                         provider='joinquant', level=IntervalLevel.LEVEL_1DAY)
        day_bull_selector.add_filter_factor(day_bull_factor)

        self.selectors.append(week_bull_selector)
        self.selectors.append(day_bull_selector)

    def filter_selector_long_targets(self, timestamp, selector: TargetSelector, long_targets: List[str]) -> List[str]:
        # 选择器选出的个股，再做进一步处理
        if selector.level == IntervalLevel.LEVEL_1DAY:
            if not long_targets:
                return None

            # 选择营收有增长的，并排序
            start_timestamp = timestamp - datetime.timedelta(100)
            df = FinanceFactor.query_data(entity_ids=long_targets, order=FinanceFactor.op_income_growth_yoy.desc(),
                                          filters=[FinanceFactor.op_income_growth_yoy > 0],
                                          start_timestamp=start_timestamp,
                                          end_timestamp=timestamp,
                                          columns=[FinanceFactor.entity_id, FinanceFactor.op_income_growth_yoy])
            if pd_is_not_null(df):
                return df['entity_id'].iloc[:10].tolist()
            return None
        return long_targets

    def filter_selector_short_targets(self, timestamp, selector: TargetSelector, short_targets: List[str]) -> List[str]:
        return short_targets


if __name__ == '__main__':
    trader = MultipleLevelBullTrader(start_timestamp='2019-01-01', end_timestamp='2020-01-01')
    trader.run()
