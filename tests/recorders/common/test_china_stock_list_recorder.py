# -*- coding: utf-8 -*-
from ...context import init_test_context

init_test_context()

from zvt.recorders.exchange.china_stock_list_spider import ExchangeChinaStockListRecorder


def test_china_stock_recorder():
    recorder = ExchangeChinaStockListRecorder()

    try:
        recorder.run()
    except:
        assert False
