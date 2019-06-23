# -*- coding: utf-8 -*-
from ..context import init_context

init_context()

from zvt.factors.technical_factor import TechnicalFactor, CrossMaFactor
from zvt.domain import SecurityType, TradingLevel, Provider


def test_ma():
    factor = TechnicalFactor(security_type=SecurityType.stock,
                             codes=['000338'],
                             start_timestamp='2019-01-01',
                             end_timestamp='2019-06-10',
                             level=TradingLevel.LEVEL_1DAY,
                             provider=Provider.JOINQUANT,
                             indicators=['ma', 'ma', 'ma'],
                             indicators_param=[{'window': 5}, {'window': 10}, {'window': 30}])

    print(factor.get_depth_df().tail())

    # compare with east money manually
    ma5 = factor.get_depth_df()['ma5']
    ma10 = factor.get_depth_df()['ma10']
    ma30 = factor.get_depth_df()['ma30']

    assert round(ma5.loc[('stock_sz_000338', '2019-06-10')], 2) == 11.48
    assert round(ma10.loc[('stock_sz_000338', '2019-06-10')], 2) == 11.69
    assert round(ma30.loc[('stock_sz_000338', '2019-06-10')], 2) == 11.79

    factor.move_on(to_timestamp='2019-06-17')
    ma5 = factor.get_depth_df()['ma5']
    ma10 = factor.get_depth_df()['ma10']
    ma30 = factor.get_depth_df()['ma30']

    assert round(ma5.loc[('stock_sz_000338', '2019-06-17')], 2) == 12.33
    assert round(ma10.loc[('stock_sz_000338', '2019-06-17')], 2) == 11.91
    assert round(ma30.loc[('stock_sz_000338', '2019-06-17')], 2) == 11.76


def test_macd():
    factor = TechnicalFactor(security_type=SecurityType.stock,
                             codes=['000338'],
                             start_timestamp='2019-01-01',
                             end_timestamp='2019-06-10',
                             level=TradingLevel.LEVEL_1DAY,
                             provider=Provider.JOINQUANT,
                             indicators=['macd'],
                             indicators_param=[{'slow': 26, 'fast': 12, 'n': 9}])

    print(factor.get_depth_df().tail())

    # compare with east money manually
    diff = factor.get_depth_df()['diff']
    dea = factor.get_depth_df()['dea']
    macd = factor.get_depth_df()['macd']

    assert round(diff.loc[('stock_sz_000338', '2019-06-10')], 2) == -0.15
    assert round(dea.loc[('stock_sz_000338', '2019-06-10')], 2) == -0.16
    assert round(macd.loc[('stock_sz_000338', '2019-06-10')], 2) == 0.02

    factor.move_on(to_timestamp='2019-06-17')
    diff = factor.get_depth_df()['diff']
    dea = factor.get_depth_df()['dea']
    macd = factor.get_depth_df()['macd']

    assert round(diff.loc[('stock_sz_000338', '2019-06-17')], 2) == 0.07
    assert round(dea.loc[('stock_sz_000338', '2019-06-17')], 2) == -0.03
    assert round(macd.loc[('stock_sz_000338', '2019-06-17')], 2) == 0.19


def test_cross_ma():
    factor = CrossMaFactor(security_type=SecurityType.stock,
                           codes=['000338'],
                           start_timestamp='2019-01-01',
                           end_timestamp='2019-06-10',
                           level=TradingLevel.LEVEL_1DAY,
                           provider=Provider.JOINQUANT,
                           short_window=5,
                           long_window=10)
    print(factor.get_depth_df().tail())
    print(factor.get_result_df().tail())

    score = factor.get_result_df()['score']

    assert score[('stock_sz_000338', '2019-06-03')] == True
    assert score[('stock_sz_000338', '2019-06-04')] == True
    assert score[('stock_sz_000338', '2019-06-05')] == False
    assert score[('stock_sz_000338', '2019-06-06')] == False
    assert score[('stock_sz_000338', '2019-06-10')] == False

    factor.move_on()
    score = factor.get_result_df()['score']
    assert score[('stock_sz_000338', '2019-06-17')] == True
