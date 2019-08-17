# -*- coding: utf-8 -*-
import enum


class TradingSignalType(enum.Enum):
    trading_signal_open_long = 'trading_signal_open_long'
    trading_signal_open_short = 'trading_signal_open_short'
    trading_signal_keep_long = 'trading_signal_keep_long'
    trading_signal_keep_short = 'trading_signal_keep_short'
    trading_signal_close_long = 'trading_signal_close_long'
    trading_signal_close_short = 'trading_signal_close_short'


class TradingSignal:
    def __init__(self, entity_id, the_timestamp, trading_level, trading_signal_type, position_pct=0, order_money=0):
        """

        :param entity_id:
        :type entity_id:
        :param the_timestamp:
        :type the_timestamp:
        :param trading_level:
        :type trading_level: IntervalLevel
        :param trading_signal_type:
        :type trading_signal_type: TradingSignalType
        """
        self.entity_id = entity_id
        self.the_timestamp = the_timestamp
        self.trading_level = trading_level
        self.trading_signal_type = trading_signal_type

        # use position_pct or order_money
        self.position_pct = position_pct

        # when close the position,just use position_pct
        self.order_money = order_money

    def __repr__(self) -> str:
        return 'entity_id:{},the_timestamp:{},trading_level:{},trading_signal_type:{},position_pct:{},order_money:{}'.format(
            self.entity_id, self.the_timestamp, self.trading_level, self.trading_signal_type.value, self.position_pct,
            self.order_money)


class TradingListener(object):
    def on_trading_signal(self, trading_signal: TradingSignal):
        raise NotImplementedError

    def on_trading_open(self, timestamp):
        raise NotImplementedError

    def on_trading_close(self, timestamp):
        raise NotImplementedError


class StateListener(object):
    def on_state(self, state):
        pass
