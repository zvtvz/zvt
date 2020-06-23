# -*- coding: utf-8 -*-
from zvt.api.quote import get_kdata
from zvt.contract import IntervalLevel


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

    se = df.loc['2019-04-08']
    # make sure our fq is ok
    assert round(se['open'], 2) <= 12.86
    assert round(se['high'], 2) <= 14.16
    assert round(se['low'], 2) <= 12.86
    assert round(se['close'], 2) <= 14.08


def test_jq_1d_hfq_kdata():
    df = get_kdata(entity_id='stock_sz_000338', provider='joinquant', level=IntervalLevel.LEVEL_1DAY, adjust_type='hfq')
    se = df.loc['2019-04-08']
    print(se)
    assert round(se['open'], 2) == 249.29
    assert round(se['high'], 2) == 273.68
    assert round(se['low'], 2) == 249.29
    assert round(se['close'], 2) == 272.18
