# -*- coding: utf-8 -*-
from zvdata import IntervalLevel
from zvt.recorders.ccxt.coin_kdata_recorder import CoinKdataRecorder
from zvt.recorders.ccxt.coin_meta_recorder import CoinMetaRecorder
from ...context import init_test_context

init_test_context()


def test_coin_meta_recorder():
    recorder = CoinMetaRecorder()

    try:
        recorder.run()
    except:
        assert False


def test_1d_kdata_recorder():
    recorder = CoinKdataRecorder(exchanges=['binance'], codes=['EOS/USDT'], level=IntervalLevel.LEVEL_1DAY,
                                 real_time=False)
    try:
        recorder.run()
    except:
        assert False


def test_1h_kdata_recorder():
    recorder = CoinKdataRecorder(exchanges=['binance'], codes=['EOS/USDT'], level=IntervalLevel.LEVEL_1HOUR,
                                 real_time=False)
    try:
        recorder.run()
    except:
        assert False
