# -*- coding: utf-8 -*-
from ...context import init_test_context

init_test_context()

from zvt.recorders.eastmoney.meta.china_stock_meta_recorder import ChinaStockMetaRecorder

from zvt.settings import SAMPLE_STOCK_CODES


def test_meta_recorder():
    recorder = ChinaStockMetaRecorder(codes=SAMPLE_STOCK_CODES)
    try:
        recorder.run()
    except:
        assert False
