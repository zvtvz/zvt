# -*- coding: utf-8 -*-
from zvdata import IntervalLevel
from zvt.factors.algorithm import MaTransformer, MacdTransformer
from zvt.factors.ma.ma_factor import CrossMaFactor
from ..context import init_test_context

init_test_context()

from zvt.factors.technical_factor import TechnicalFactor


def test_ma():
    factor = TechnicalFactor(entity_type='stock',
                             codes=['000338'],
                             start_timestamp='2019-01-01',
                             end_timestamp='2019-06-10',
                             level=IntervalLevel.LEVEL_1DAY,
                             provider='joinquant',
                             computing_window=30,
                             transformer=MaTransformer(windows=[5, 10, 30]))

    print(factor.get_factor_df().tail())

    # compare with east money manually
    ma5 = factor.get_factor_df()['ma5']
    ma10 = factor.get_factor_df()['ma10']
    ma30 = factor.get_factor_df()['ma30']

    assert round(ma5.loc[('stock_sz_000338', '2019-06-10')], 2) <= 11.23
    assert round(ma10.loc[('stock_sz_000338', '2019-06-10')], 2) <= 11.43
    assert round(ma30.loc[('stock_sz_000338', '2019-06-10')], 2) <= 11.52

    factor.move_on(to_timestamp='2019-06-17')
    ma5 = factor.get_factor_df()['ma5']
    ma10 = factor.get_factor_df()['ma10']
    ma30 = factor.get_factor_df()['ma30']

    assert round(ma5.loc[('stock_sz_000338', '2019-06-17')], 2) <= 12.06
    assert round(ma10.loc[('stock_sz_000338', '2019-06-17')], 2) <= 11.64
    assert round(ma30.loc[('stock_sz_000338', '2019-06-17')], 2) <= 11.50


def test_macd():
    factor = TechnicalFactor(entity_type='stock',
                             codes=['000338'],
                             start_timestamp='2019-01-01',
                             end_timestamp='2019-06-10',
                             level=IntervalLevel.LEVEL_1DAY,
                             provider='joinquant',
                             computing_window=None,
                             transformer=MacdTransformer())

    print(factor.get_factor_df().tail())

    # compare with east money manually
    diff = factor.get_factor_df()['diff']
    dea = factor.get_factor_df()['dea']
    macd = factor.get_factor_df()['macd']

    assert round(diff.loc[('stock_sz_000338', '2019-06-10')], 2) == -0.14
    assert round(dea.loc[('stock_sz_000338', '2019-06-10')], 2) == -0.15
    assert round(macd.loc[('stock_sz_000338', '2019-06-10')], 2) == 0.02

    factor.move_on(to_timestamp='2019-06-17')
    diff = factor.get_factor_df()['diff']
    dea = factor.get_factor_df()['dea']
    macd = factor.get_factor_df()['macd']

    assert round(diff.loc[('stock_sz_000338', '2019-06-17')], 2) == 0.06
    assert round(dea.loc[('stock_sz_000338', '2019-06-17')], 2) == -0.03
    assert round(macd.loc[('stock_sz_000338', '2019-06-17')], 2) == 0.19


def test_cross_ma():
    factor = CrossMaFactor(entity_type='stock',
                           codes=['000338'],
                           start_timestamp='2019-01-01',
                           end_timestamp='2019-06-10',
                           level=IntervalLevel.LEVEL_1DAY,
                           provider='joinquant',
                           windows=[5,10])
    print(factor.get_factor_df().tail())
    print(factor.get_result_df().tail())

    score = factor.get_result_df()['score']

    assert score[('stock_sz_000338', '2019-06-03')] == True
    assert score[('stock_sz_000338', '2019-06-04')] == True
    assert ('stock_sz_000338', '2019-06-05') not in score or score[('stock_sz_000338', '2019-06-05')] == False
    assert ('stock_sz_000338', '2019-06-06') not in score or score[('stock_sz_000338', '2019-06-06')] == False
    assert ('stock_sz_000338', '2019-06-10') not in score or score[('stock_sz_000338', '2019-06-10')] == False

    factor.move_on()
    score = factor.get_result_df()['score']
    assert score[('stock_sz_000338', '2019-06-17')] == True
