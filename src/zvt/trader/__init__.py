# -*- coding: utf-8 -*-
from enum import Enum
from typing import Union, List

import pandas as pd

from zvt.contract import IntervalLevel
from zvt.utils.decorator import to_string


class TradingSignalType(Enum):
    open_long = "open_long"
    open_short = "open_short"
    keep_long = "keep_long"
    keep_short = "keep_short"
    close_long = "close_long"
    close_short = "close_short"


class OrderType(Enum):
    order_long = "order_long"
    order_short = "order_short"
    order_close_long = "order_close_long"
    order_close_short = "order_close_short"


def trading_signal_type_to_order_type(trading_signal_type):
    if trading_signal_type == TradingSignalType.open_long:
        return OrderType.order_long
    elif trading_signal_type == TradingSignalType.open_short:
        return OrderType.order_short
    elif trading_signal_type == TradingSignalType.close_long:
        return OrderType.order_close_long
    elif trading_signal_type == TradingSignalType.close_short:
        return OrderType.order_close_short


@to_string
class TradingSignal:
    def __init__(
        self,
        entity_id: str,
        due_timestamp: Union[str, pd.Timestamp],
        happen_timestamp: Union[str, pd.Timestamp],
        trading_level: IntervalLevel,
        trading_signal_type: TradingSignalType,
        position_pct: float = None,
        order_money: float = None,
        order_amount: int = None,
    ):
        """

        :param entity_id: the entity id
        :param due_timestamp: the signal due time
        :param happen_timestamp: the time when generating the signal
        :param trading_level: the level
        :param trading_signal_type:
        :param position_pct: percentage of account to order
        :param order_money: money to order
        :param order_amount: amount to order
        """
        self.entity_id = entity_id
        self.due_timestamp = due_timestamp
        self.happen_timestamp = happen_timestamp
        self.trading_level = trading_level
        self.trading_signal_type = trading_signal_type

        if len([x for x in (position_pct, order_money, order_amount) if x is not None]) != 1:
            assert False
        # use position_pct or order_money or order_amount
        self.position_pct = position_pct
        # when close the position,just use position_pct
        self.order_money = order_money
        self.order_amount = order_amount


class TradingListener(object):
    def on_trading_open(self, timestamp):
        raise NotImplementedError

    def on_trading_signals(self, trading_signals: List[TradingSignal]):
        raise NotImplementedError

    def on_trading_close(self, timestamp):
        raise NotImplementedError

    def on_trading_finish(self, timestamp):
        raise NotImplementedError

    def on_trading_error(self, timestamp, error):
        raise NotImplementedError


class AccountService(TradingListener):
    def get_positions(self):
        pass

    def get_current_position(self, entity_id, create_if_not_exist=False):
        """
        overwrite it to provide your real position

        :param entity_id:
        """
        pass

    def get_current_account(self):
        pass

    def order_by_position_pct(
        self,
        entity_id,
        order_price,
        order_timestamp,
        order_type,
        order_position_pct: float,
    ):
        pass

    def order_by_money(
        self,
        entity_id,
        order_price,
        order_timestamp,
        order_type,
        order_money,
    ):
        pass

    def order_by_amount(
        self,
        entity_id,
        order_price,
        order_timestamp,
        order_type,
        order_amount,
    ):
        pass


# the __all__ is generated
__all__ = ["TradingSignalType", "TradingListener", "OrderType", "AccountService", "trading_signal_type_to_order_type"]

# __init__.py structure:
# common code of the package
# export interface in __all__ which contains __all__ of its sub modules

# import all from submodule trader
from .trader import *
from .trader import __all__ as _trader_all

__all__ += _trader_all

# import all from submodule errors
from .errors import *
from .errors import __all__ as _errors_all

__all__ += _errors_all

# import all from submodule account
from .sim_account import *
from .sim_account import __all__ as _account_all

__all__ += _account_all
