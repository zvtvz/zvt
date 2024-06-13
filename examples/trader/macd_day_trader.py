# -*- coding: utf-8 -*-
from typing import List, Tuple

import pandas as pd

from zvt.contract import IntervalLevel
from zvt.contract.factor import Factor
from zvt.factors.macd.macd_factor import GoldCrossFactor
from zvt.trader import TradingSignal
from zvt.trader.trader import StockTrader

# 依赖数据
# data_schema: Stock1dHfqKdata
# provider: joinquant
from zvt.utils.time_utils import date_time_by_interval


class MacdDayTrader(StockTrader):
    def init_factors(
        self, entity_ids, entity_schema, exchanges, codes, start_timestamp, end_timestamp, adjust_type=None
    ):
        # 日线策略
        start_timestamp = date_time_by_interval(start_timestamp, -50)
        return [
            GoldCrossFactor(
                entity_ids=entity_ids,
                entity_schema=entity_schema,
                exchanges=exchanges,
                codes=codes,
                start_timestamp=start_timestamp,
                end_timestamp=end_timestamp,
                provider="joinquant",
                level=IntervalLevel.LEVEL_1DAY,
            )
        ]

    def on_profit_control(self):
        # 覆盖该函数做止盈 止损
        return super().on_profit_control()

    def on_time(self, timestamp: pd.Timestamp):
        # 对selectors选出的标的做进一步处理，或者不使用selector完全自己根据时间和数据生成交易信号
        super().on_time(timestamp)

    def on_trading_signals(self, trading_signals: List[TradingSignal]):
        # 批量处理交易信号，比如连接交易接口，发邮件，微信推送等
        super().on_trading_signals(trading_signals)

    def on_trading_open(self, timestamp):
        # 开盘自定义逻辑
        super().on_trading_open(timestamp)

    def on_trading_close(self, timestamp):
        # 收盘自定义逻辑
        super().on_trading_close(timestamp)

    def on_trading_finish(self, timestamp):
        # 策略退出自定义逻辑
        super().on_trading_finish(timestamp)

    def on_trading_error(self, timestamp, error):
        # 出错处理
        super().on_trading_error(timestamp, error)

    def long_position_control(self):
        # 多头仓位管理
        return super().long_position_control()

    def short_position_control(self):
        # 空头仓位管理
        return super().short_position_control()

    def on_factor_targets_filtered(
        self, timestamp, level, factor: Factor, long_targets: List[str], short_targets: List[str]
    ) -> Tuple[List[str], List[str]]:
        # 过滤某级别选出的 标的
        return super().on_factor_targets_filtered(timestamp, level, factor, long_targets, short_targets)


if __name__ == "__main__":
    trader = MacdDayTrader(start_timestamp="2019-01-01", end_timestamp="2020-01-01")
    trader.run()
    # f = VolFactor(start_timestamp='2020-01-01', end_timestamp='2020-04-01')
    # print(f.result_df)
