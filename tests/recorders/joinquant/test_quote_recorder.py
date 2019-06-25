# -*- coding: utf-8 -*-
from ...context import init_context

init_context()

from zvt.settings import SAMPLE_STOCK_CODES
from zvt.domain import TradingLevel
from zvt.recorders.joinquant.quotes.jq_china_stock__kdata_recorder import JQChinaStockKdataRecorder


def test_1d_kdata_recorder():
    recorder = JQChinaStockKdataRecorder(codes=SAMPLE_STOCK_CODES, sleeping_time=0, level=TradingLevel.LEVEL_1DAY)
    try:
        recorder.run()
    except:
        assert False


def test_1h_kdata_recorder():
    recorder = JQChinaStockKdataRecorder(codes=SAMPLE_STOCK_CODES, sleeping_time=0, level=TradingLevel.LEVEL_1HOUR,
                                         start_timestamp='2019-06-01')
    try:
        recorder.run()
    except:
        assert False


def test_5m_kdata_recorder():
    recorder = JQChinaStockKdataRecorder(codes=SAMPLE_STOCK_CODES, sleeping_time=0, level=TradingLevel.LEVEL_5MIN,
                                         start_timestamp='2019-06-01')
    try:
        recorder.run()
    except:
        assert False
