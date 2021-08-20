# -*- coding: utf-8 -*-
from ...context import init_test_context

init_test_context()

from zvt.recorders.eastmoney import EastmoneyChinaStockListRecorder


def test_china_stock_recorder():
    recorder = EastmoneyChinaStockListRecorder()

    try:
        recorder.run()
    except:
        assert False
