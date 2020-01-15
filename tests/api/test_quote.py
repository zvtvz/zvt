# -*- coding: utf-8 -*-
from zvdata import IntervalLevel
from zvt.api.quote import get_kdata


def test_jq_1mon_kdata():
    df = get_kdata(entity_id='stock_sz_000338', provider='joinquant', level=IntervalLevel.LEVEL_1MON)
    se = df.loc['2010-01-29']
    # make sure our fq is ok
    assert round(se['open'], 2) <= 5.44
    assert round(se['high'], 2) <= 6.43
    assert round(se['low'], 2) <= 5.2
    assert round(se['close'], 2) <= 5.45


def test_jq_1wk_kdata():
    df = get_kdata(entity_id='stock_sz_000338', provider='joinquant', level=IntervalLevel.LEVEL_1WEEK)
    print(df)


def test_jq_1d_kdata():
    df = get_kdata(entity_id='stock_sz_000338', provider='joinquant', level=IntervalLevel.LEVEL_1DAY)
    print(df)
