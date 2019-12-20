# -*- coding: utf-8 -*-
from ...context import init_test_context

init_test_context()

from zvt.recorders.common.china_stock_list_spider import ChinaStockListRecorder


def test_china_stock_recorder():
    recorder = ChinaStockListRecorder()

    try:
        recorder.run()
    except:
        assert False
