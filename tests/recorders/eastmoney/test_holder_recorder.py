# -*- coding: utf-8 -*-
from ...context import init_test_context

init_test_context()

from zvt.settings import SAMPLE_STOCK_CODES

from zvt.recorders.eastmoney.holder.top_ten_holder_recorder import TopTenHolderRecorder
from zvt.recorders.eastmoney.holder.top_ten_tradable_holder_recorder import TopTenTradableHolderRecorder


def test_top_ten_holder_recorder():
    recorder = TopTenHolderRecorder(codes=SAMPLE_STOCK_CODES)
    try:
        recorder.run()
    except:
        assert False


def test_top_ten_tradable_holder_recorder():
    recorder = TopTenTradableHolderRecorder(codes=SAMPLE_STOCK_CODES)
    try:
        recorder.run()
    except:
        assert False
