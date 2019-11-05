# -*- coding: utf-8 -*-
from zvdata import IntervalLevel
from zvt.api.quote import get_indices, get_kdata
from zvt.domain import StockCategory


def test_get_indices():
    df = get_indices(provider='sina', block_category=StockCategory.industry)
    print(df)

    df = get_indices(provider='eastmoney', block_category=StockCategory.industry)
    print(df)


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
    se = df.loc['2019-04-19']
    # make sure our fq is ok
    assert round(se['open'], 2) <= 13.28
    assert round(se['high'], 2) <= 13.90
    assert round(se['low'], 2) <= 12.36
    assert round(se['close'], 2) <= 13.30


def test_jq_1d_kdata():
    df = get_kdata(entity_id='stock_sz_000338', provider='joinquant', level=IntervalLevel.LEVEL_1DAY)
    se = df.loc['2019-04-19']
    # make sure our fq is ok
    assert round(se['open'], 2) <= 12.93
    assert round(se['high'], 2) <= 13.52
    assert round(se['low'], 2) <= 12.89
    assert round(se['close'], 2) <= 13.33
