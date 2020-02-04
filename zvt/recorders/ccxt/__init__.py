# -*- coding: utf-8 -*-
from zvdata import IntervalLevel


def to_ccxt_trading_level(trading_level: IntervalLevel):
    return trading_level.value


from zvt.recorders.ccxt.coin_tick_recorder import *
from zvt.recorders.ccxt.coin_meta_recorder import *
from zvt.recorders.ccxt.coin_kdata_recorder import *
