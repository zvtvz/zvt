# -*- coding: utf-8 -*-
from ...context import init_test_context

init_test_context()

from zvdata import IntervalLevel

from zvt.settings import SAMPLE_STOCK_CODES
from zvt.recorders.joinquant.quotes.jq_stock_kdata_recorder import ChinaStockKdataRecorder


def test_1wk_kdata_recorder():
    recorder = ChinaStockKdataRecorder(codes=SAMPLE_STOCK_CODES, sleeping_time=0, level=IntervalLevel.LEVEL_1WEEK,
                                       real_time=False)
    try:
        recorder.run()
    except:
        assert False


def test_1mon_kdata_recorder():
    recorder = ChinaStockKdataRecorder(codes=SAMPLE_STOCK_CODES, sleeping_time=0, level=IntervalLevel.LEVEL_1MON,
                                       real_time=False)
    try:
        recorder.run()
    except:
        assert False


def test_1d_kdata_recorder():
    recorder = ChinaStockKdataRecorder(codes=SAMPLE_STOCK_CODES, sleeping_time=0, level=IntervalLevel.LEVEL_1DAY,
                                       real_time=False)
    try:
        recorder.run()
    except:
        assert False


def test_1h_kdata_recorder():
    recorder = ChinaStockKdataRecorder(codes=['000338'], sleeping_time=0, level=IntervalLevel.LEVEL_1HOUR,
                                       real_time=False, start_timestamp='2019-01-01')
    try:
        recorder.run()
    except:
        assert False


def test_5m_kdata_recorder():
    recorder = ChinaStockKdataRecorder(codes=['000338'], sleeping_time=0, level=IntervalLevel.LEVEL_5MIN,
                                       real_time=False, start_timestamp='2019-01-01')
    try:
        recorder.run()
    except:
        assert False
