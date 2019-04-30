# -*- coding: utf-8 -*-
import enum


class TradingSignalType(enum.Enum):
    trading_signal_open_long = 'trading_signal_open_long'
    trading_signal_open_short = 'trading_signal_open_oshort'
    trading_signal_keep_long = 'trading_signal_keep_long'
    trading_signal_keep_short = 'trading_signal_keep_short'
    trading_signal_close_long = 'trading_signal_close_long'
    trading_signal_close_short = 'trading_signal_close_short'


class TradingSignal:
    def __init__(self, security_id, start_timestamp, end_timestamp, trading_signal_type, current_price):
        self.security_id = security_id
        self.start_timestamp = start_timestamp
        self.end_timestamp = end_timestamp
        self.trading_signal_type = trading_signal_type
        self.current_price = current_price


class TradingSignalListener(object):
    def on_trading_signal(self, trading_signal: TradingSignal):
        pass


class StateListener(object):
    def on_state(self, state):
        pass
