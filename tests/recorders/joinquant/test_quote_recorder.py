# -*- coding: utf-8 -*-
from zvdata.structs import IntervalLevel
from zvdata.utils.time_utils import day_offset_today
from ...context import init_context

init_context()

from zvt.settings import SAMPLE_STOCK_CODES
from zvt.recorders.joinquant.quotes.jq_china_stock__kdata_recorder import JQChinaStockKdataRecorder


def test_1d_kdata_recorder():
    recorder = JQChinaStockKdataRecorder(codes=SAMPLE_STOCK_CODES, sleeping_time=0, level=IntervalLevel.LEVEL_1DAY,
                                         one_shot=True)
    try:
        recorder.run()
    except:
        assert False


def test_1h_kdata_recorder():
    start_timestamp = day_offset_today(-5)
    recorder = JQChinaStockKdataRecorder(codes=SAMPLE_STOCK_CODES, sleeping_time=0, level=IntervalLevel.LEVEL_1HOUR,
                                         start_timestamp=start_timestamp, one_shot=True)
    try:
        recorder.run()
    except:
        assert False


def test_5m_kdata_recorder():
    start_timestamp = day_offset_today(-5)

    recorder = JQChinaStockKdataRecorder(codes=SAMPLE_STOCK_CODES, sleeping_time=0, level=IntervalLevel.LEVEL_5MIN,
                                         start_timestamp=start_timestamp, one_shot=True)
    try:
        recorder.run()
    except:
        assert False
