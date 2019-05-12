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
    def __init__(self, security_id, the_timestamp, trading_level, trading_signal_type, position_pct):
        """

        :param security_id:
        :type security_id:
        :param the_timestamp:
        :type the_timestamp:
        :param trading_level:
        :type trading_level: TradingLevel
        :param trading_signal_type:
        :type trading_signal_type: TradingSignalType
        """
        self.security_id = security_id
        self.the_timestamp = the_timestamp
        self.trading_level = trading_level
        self.trading_signal_type = trading_signal_type
        self.position_pct = position_pct


class TradingSignalListener(object):
    def on_trading_signal(self, trading_signal: TradingSignal):
        pass


class StateListener(object):
    def on_state(self, state):
        pass
