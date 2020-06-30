# -*- coding: utf-8 -*-
from typing import List, Union

import pandas as pd

from zvt.contract import IntervalLevel, EntityMixin
from zvt.domain import Stock1dKdata, Stock
from zvt.factors import TargetSelector, BullFactor, ScoreFactor, Transformer, Accumulator
from zvt.factors.algorithm import RankScorer
from zvt.trader.trader import StockTrader, LimitSelectorsComparator


class VolComparator(LimitSelectorsComparator):
    def __init__(self, selectors: List[TargetSelector], limit=3000) -> None:
        super().__init__(selectors, limit)

    def make_decision(self, timestamp, trading_level: IntervalLevel):
        longs, shorts = super().make_decision(timestamp, trading_level)
        if longs or shorts:
            # 成交超过1亿的前300个股
            df = Stock1dKdata.query_data(start_timestamp=timestamp, end_timestamp=timestamp,
                                         columns=[Stock1dKdata.entity_id], filters=[Stock1dKdata.turnover > 100000000],
                                         limit=300, order=Stock1dKdata.volume.desc())
            longs1 = set(df['entity_id'].to_list())
            long_targets = set(longs) & longs1

            if shorts:
                all = Stock.query_data(columns=[Stock.entity_id])
                short_targets = set(shorts) | (set(all['entity_id'].to_list()) - longs1)
            else:
                short_targets = shorts

            return long_targets, short_targets
        return longs, shorts


class VolFactor(ScoreFactor):
    def __init__(self, entity_schema: EntityMixin = Stock, provider: str = None,
                 entity_provider: str = None, entity_ids: List[str] = None, exchanges: List[str] = None,
                 codes: List[str] = None, the_timestamp: Union[str, pd.Timestamp] = None,
                 start_timestamp: Union[str, pd.Timestamp] = None, end_timestamp: Union[str, pd.Timestamp] = None,
                 filters: List = None, order: object = None, limit: int = None,
                 level: Union[str, IntervalLevel] = IntervalLevel.LEVEL_1DAY, category_field: str = 'entity_id',
                 time_field: str = 'timestamp', computing_window: int = None, keep_all_timestamp: bool = False,
                 fill_method: str = 'ffill', effective_number: int = None, transformer: Transformer = None,
                 accumulator: Accumulator = None, need_persist: bool = False, dry_run: bool = False) -> None:
        super().__init__(Stock1dKdata, entity_schema, provider, entity_provider, entity_ids, exchanges, codes,
                         the_timestamp, start_timestamp, end_timestamp, [Stock1dKdata.turnover], filters, order, limit,
                         level, category_field, time_field, computing_window, keep_all_timestamp, fill_method,
                         effective_number, transformer, accumulator, need_persist, dry_run, RankScorer(ascending=True))

    def pre_compute(self):
        super().pre_compute()
        self.pipe_df = self.pipe_df[['turnover']]


class VolMacdTrader(StockTrader):

    def init_selectors(self, entity_ids, entity_schema, exchanges, codes, start_timestamp, end_timestamp):
        # 周线策略
        week_bull_selector = TargetSelector(entity_ids=entity_ids, entity_schema=entity_schema, exchanges=exchanges,
                                            codes=codes, start_timestamp=start_timestamp, end_timestamp=end_timestamp,
                                            provider='joinquant', level=IntervalLevel.LEVEL_1WEEK)
        week_bull_factor = BullFactor(entity_ids=entity_ids, entity_schema=entity_schema, exchanges=exchanges,
                                      codes=codes, start_timestamp=start_timestamp, end_timestamp=end_timestamp,
                                      provider='joinquant', level=IntervalLevel.LEVEL_1WEEK)
        week_bull_selector.add_filter_factor(week_bull_factor)

        # 日线策略
        day_bull_selector = TargetSelector(entity_ids=entity_ids, entity_schema=entity_schema, exchanges=exchanges,
                                           codes=codes, start_timestamp=start_timestamp, end_timestamp=end_timestamp,
                                           provider='joinquant', level=IntervalLevel.LEVEL_1DAY)
        day_bull_factor = BullFactor(entity_ids=entity_ids, entity_schema=entity_schema, exchanges=exchanges,
                                     codes=codes, start_timestamp=start_timestamp, end_timestamp=end_timestamp,
                                     provider='joinquant', level=IntervalLevel.LEVEL_1DAY)
        day_vol_factor = VolFactor(entity_ids=entity_ids, entity_schema=entity_schema, exchanges=exchanges,
                                   codes=codes, start_timestamp=start_timestamp, end_timestamp=end_timestamp,
                                   provider='joinquant', level=IntervalLevel.LEVEL_1DAY)
        day_bull_selector.add_filter_factor(day_bull_factor)
        day_bull_selector.add_score_factor(day_vol_factor)

        self.selectors.append(week_bull_selector)
        self.selectors.append(day_bull_selector)

    def init_selectors_comparator(self):
        return LimitSelectorsComparator(self.selectors, limit=50)


if __name__ == '__main__':
    trader = VolMacdTrader(start_timestamp='2017-01-01', end_timestamp='2017-06-01')
    trader.run()
    # f = VolFactor(start_timestamp='2020-01-01', end_timestamp='2020-04-01')
    # print(f.result_df)
