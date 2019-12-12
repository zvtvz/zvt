# -*- coding: utf-8 -*-
from zvdata import IntervalLevel


def to_ccxt_trading_level(trading_level: IntervalLevel):
    return trading_level.value


from .coin_kdata_recorder import CoinKdataRecorder
from .coin_meta_recorder import CoinMetaRecorder
from .coin_tick_recorder import CoinTickRecorder

__all__ = ['CoinKdataRecorder', 'CoinMetaRecorder', 'CoinTickRecorder']
