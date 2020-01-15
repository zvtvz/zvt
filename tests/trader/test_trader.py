# -*- coding: utf-8 -*-
from zvdata import IntervalLevel
from zvt.samples import MyMaTrader


def test_basic_trader():
    try:
        MyMaTrader(codes=['000338'], level=IntervalLevel.LEVEL_1DAY, start_timestamp='2018-01-01',
                   end_timestamp='2019-06-30', trader_name='000338_ma_trader', draw_result=False).run()
    except:
        assert False
