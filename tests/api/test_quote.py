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
    assert round(se['qfq_open'], 2) == 5.51
    assert round(se['qfq_high'], 2) == 6.51
    assert round(se['qfq_low'], 2) == 5.26
    assert round(se['qfq_close'], 2) == 5.52

    se = df.loc['2015-06-30']
    assert se['qfq_open'] == 6.63
    assert se['qfq_high'] == 8.06
    assert se['qfq_low'] == 5.65
    assert se['qfq_close'] == 6.81


def test_jq_1wk_kdata():
    df = get_kdata(entity_id='stock_sz_000338', provider='joinquant', level=IntervalLevel.LEVEL_1WEEK)
    se = df.loc['2019-04-19']
    # make sure our fq is ok
    assert round(se['qfq_open'], 2) == 13.45
    assert round(se['qfq_high'], 2) == 14.08
    assert round(se['qfq_low'], 2) == 12.52
    assert round(se['qfq_close'], 2) == 13.47


def test_jq_1d_kdata():
    df = get_kdata(entity_id='stock_sz_000338', provider='joinquant', level=IntervalLevel.LEVEL_1DAY)
    se = df.loc['2019-04-19']
    # make sure our fq is ok
    assert round(se['qfq_open'], 2) == 13.08
    assert round(se['qfq_high'], 2) == 13.68
    assert round(se['qfq_low'], 2) == 13.04
    assert round(se['qfq_close'], 2) == 13.48
