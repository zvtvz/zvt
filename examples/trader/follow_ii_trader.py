# -*- coding: utf-8 -*-
import pandas as pd

from zvt.api import get_recent_report_date
from zvt.contract import ActorType, AdjustType
from zvt.domain import StockActorSummary, Stock1dKdata, Stock
from zvt.trader import StockTrader
from zvt.utils import pd_is_not_null, is_same_date, to_pd_timestamp


class FollowIITrader(StockTrader):
    finish_date = None

    def on_time(self, timestamp: pd.Timestamp):
        recent_report_date = to_pd_timestamp(get_recent_report_date(timestamp))
        if self.finish_date and is_same_date(recent_report_date, self.finish_date):
            return
        filters = [
            StockActorSummary.actor_type == ActorType.raised_fund.value,
            StockActorSummary.report_date == recent_report_date,
        ]

        if self.entity_ids:
            filters = filters + [StockActorSummary.entity_id.in_(self.entity_ids)]

        df = StockActorSummary.query_data(filters=filters)

        if pd_is_not_null(df):
            self.logger.info(f"{df}")
            self.finish_date = recent_report_date

        long_df = df[df["change_ratio"] > 0.05]
        short_df = df[df["change_ratio"] < -0.5]
        try:
            self.trade_the_targets(
                due_timestamp=timestamp,
                happen_timestamp=timestamp,
                long_selected=set(long_df["entity_id"].to_list()),
                short_selected=set(short_df["entity_id"].to_list()),
            )
        except Exception as e:
            self.logger.error(e)


if __name__ == "__main__":
    code = "600519"
    Stock.record_data(provider="eastmoney")
    Stock1dKdata.record_data(code=code, provider="em")
    StockActorSummary.record_data(code=code, provider="em")
    FollowIITrader(
        start_timestamp="2002-01-01",
        end_timestamp="2021-01-01",
        codes=[code],
        provider="em",
        adjust_type=AdjustType.qfq,
        profit_threshold=None,
    ).run()
