# -*- coding: utf-8 -*-
from ...context import init_context

init_context()

from zvt.recorders.common.china_stock_list_spider import ChinaStockListSpider


def test_coin_meta_recorder():
    recorder = ChinaStockListSpider()

    try:
        recorder.run()
    except:
        assert False
