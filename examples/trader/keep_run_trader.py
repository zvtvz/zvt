# -*- coding: utf-8 -*-
import logging

from zvt.api import get_top_volume_entities
from zvt.api.stats import get_top_fund_holding_stocks
from zvt.api.trader_info_api import clear_trader
from zvt.contract import IntervalLevel
from zvt.factors import TargetSelector, GoldCrossFactor, BullFactor
from zvt.trader import StockTrader
from zvt.utils.time_utils import split_time_interval, next_date

logger = logging.getLogger(__name__)


class MultipleLevelTrader(StockTrader):
    def init_selectors(
        self, entity_ids, entity_schema, exchanges, codes, start_timestamp, end_timestamp, adjust_type=None
    ):
        start_timestamp = next_date(start_timestamp, -50)

        # 周线策略
        week_selector = TargetSelector(
            entity_ids=entity_ids,
            entity_schema=entity_schema,
            exchanges=exchanges,
            codes=codes,
            start_timestamp=next_date(start_timestamp, -200),
            end_timestamp=end_timestamp,
            long_threshold=0.7,
            level=IntervalLevel.LEVEL_1WEEK,
            provider="joinquant",
        )
        week_bull_factor = BullFactor(
            entity_ids=entity_ids,
            entity_schema=entity_schema,
            exchanges=exchanges,
            codes=codes,
            start_timestamp=next_date(start_timestamp, -200),
            end_timestamp=end_timestamp,
            provider="joinquant",
            level=IntervalLevel.LEVEL_1WEEK,
        )
        week_selector.add_factor(week_bull_factor)

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


if __name__ == "__main__":
    start = "2019-01-01"
    end = "2021-01-01"
    trader_name = "keep_run_trader"
    clear_trader(trader_name=trader_name)
    for time_interval in split_time_interval(start=start, end=end, interval=40):
        start_timestamp = time_interval[0]
        end_timestamp = time_interval[-1]
        # 成交量
        vol_df = get_top_volume_entities(
            entity_type="stock", start_timestamp=next_date(start_timestamp, -50), end_timestamp=start_timestamp, pct=0.3
        )
        # 机构重仓
        ii_df = get_top_fund_holding_stocks(timestamp=start_timestamp, pct=0.3, by="trading")

        current_entity_pool = list(set(vol_df.index.tolist()) & set(ii_df.index.tolist()))

        logger.info(f"current_entity_pool({len(current_entity_pool)}):{current_entity_pool}")

        trader = MultipleLevelTrader(
            start_timestamp=start_timestamp,
            end_timestamp=end_timestamp,
            entity_ids=current_entity_pool,
            trader_name=trader_name,
            keep_history=True,
            draw_result=False,
            rich_mode=False,
        )
        trader.run()
