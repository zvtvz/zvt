# -*- coding: utf-8 -*-
import enum
from typing import Union, List

import pandas as pd

from zvt.contract import IntervalLevel
from zvt.utils.decorator import to_string


class TradingSignalType(enum.Enum):
    open_long = 'open_long'
    open_short = 'open_short'
    keep_long = 'keep_long'
    keep_short = 'keep_short'
    close_long = 'close_long'
    close_short = 'close_short'


@to_string
class TradingSignal:
    def __init__(self,
                 entity_id: str,
                 due_timestamp: Union[str, pd.Timestamp],
                 happen_timestamp: Union[str, pd.Timestamp],
                 trading_level: IntervalLevel,
                 trading_signal_type: TradingSignalType,
                 position_pct: float = 0,
                 order_money: float = 0):
        self.entity_id = entity_id
        self.due_timestamp = due_timestamp
        self.happen_timestamp = happen_timestamp
        self.trading_level = trading_level
        self.trading_signal_type = trading_signal_type

        # use position_pct or order_money
        self.position_pct = position_pct

        # when close the position,just use position_pct
        self.order_money = order_money


class TradingListener(object):
    def on_trading_signals(self, trading_signals: List[TradingSignal]):
        raise NotImplementedError

    def on_trading_signal(self, trading_signal: TradingSignal):
        raise NotImplementedError

    def on_trading_open(self, timestamp):
        raise NotImplementedError

    def on_trading_close(self, timestamp):
        raise NotImplementedError

    def on_trading_finish(self, timestamp):
        raise NotImplementedError

    def on_trading_error(self, timestamp, error):
        raise NotImplementedError
# the __all__ is generated
__all__ = ['TradingSignalType', 'TradingListener']

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
from .account import *
from .account import __all__ as _account_all
__all__ += _account_all