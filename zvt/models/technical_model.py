# -*- coding: utf-8 -*-
import enum

from talib import abstract

from zvt.trader import TradingSignal, TradingSignalType
from zvt.trader.model import Model, ModelType

SMA = abstract.Function('sma')


class ShortLongStatus(enum.Enum):
    SHORT_ON_LONG = 1
    LONG_ON_SHORT = -1
    SHORT_EQ_LONG = 0


class CrossMaModel(Model):
    short_period = 5
    long_period = 10
    last_status = None
    model_type = ModelType.TECHNICAL_MODEL

    # keep_status = []

    def make_decision(self):
        self.current_trading_signal = None
        if len(self.history_data) < 10:
            return
        ma_short = SMA(self.history_data, self.short_period)[-1]
        ma_long = SMA(self.history_data, self.long_period)[-1]

        if ma_short > ma_long:
            if self.last_status == ShortLongStatus.SHORT_ON_LONG:
                start, end = self.signal_timestamp_interval()

                self.send_trading_signal(TradingSignal(security_id=self.security_id,
                                                       current_price=self.current_data['close'],
                                                       start_timestamp=start,
                                                       end_timestamp=end,
                                                       trading_signal_type=TradingSignalType.trading_signal_keep_long
                                                       ))

            else:
                # self.keep_status.append((self.current_timestamp, ShortLongStatus.SHORT_ON_LONG))
                start, end = self.signal_timestamp_interval()

                self.send_trading_signal(TradingSignal(security_id=self.security_id,
                                                       current_price=self.current_data['close'],
                                                       start_timestamp=start, end_timestamp=end,
                                                       trading_signal_type=TradingSignalType.trading_signal_close_short))

                self.send_trading_signal(TradingSignal(security_id=self.security_id,
                                                       current_price=self.current_data['close'],
                                                       start_timestamp=start, end_timestamp=end,
                                                       trading_signal_type=TradingSignalType.trading_signal_open_long))

            self.last_status = ShortLongStatus.SHORT_ON_LONG

        if ma_short < ma_long:
            if self.last_status == ShortLongStatus.LONG_ON_SHORT:
                start, end = self.signal_timestamp_interval()

                self.send_trading_signal(TradingSignal(security_id=self.security_id,
                                                       current_price=self.current_data['close'],
                                                       start_timestamp=start, end_timestamp=end,
                                                       trading_signal_type=TradingSignalType.trading_signal_keep_short))


            else:
                # self.keep_status.append((self.current_timestamp, ShortLongStatus.LONG_ON_SHORT))
                start, end = self.signal_timestamp_interval()

                self.send_trading_signal(TradingSignal(security_id=self.security_id,
                                                       current_price=self.current_data['close'],
                                                       start_timestamp=start, end_timestamp=end,
                                                       trading_signal_type=TradingSignalType.trading_signal_close_long))

                self.send_trading_signal(TradingSignal(security_id=self.security_id,
                                                       current_price=self.current_data['close'],
                                                       start_timestamp=start, end_timestamp=end,
                                                       trading_signal_type=TradingSignalType.trading_signal_open_short))

            self.last_status = ShortLongStatus.LONG_ON_SHORT
