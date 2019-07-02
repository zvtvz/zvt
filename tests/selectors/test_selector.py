# -*- coding: utf-8 -*-
from zvt.factors.technical_factor import CrossMaFactor
from ..context import init_context

init_context()

from zvt.domain import SecurityType, TradingLevel, Provider
from zvt.selectors.technical_selector import TechnicalSelector
from zvt.selectors.selector import TargetSelector


def test_cross_ma_selector():
    security_list = ['stock_sz_000338']
    security_type = 'stock'
    start_timestamp = '2018-01-01'
    end_timestamp = '2019-06-30'
    my_selector = TargetSelector(security_list=security_list,
                                 security_type=security_type,
                                 start_timestamp=start_timestamp,
                                 end_timestamp=end_timestamp)
    # add the factors
    my_selector \
        .add_filter_factor(CrossMaFactor(security_list=security_list,
                                         security_type=security_type,
                                         start_timestamp=start_timestamp,
                                         end_timestamp=end_timestamp,
                                         level=TradingLevel.LEVEL_1DAY))
    my_selector.run()
    print(my_selector.open_long_df)
    print(my_selector.open_short_df)
    assert 'stock_sz_000338' in my_selector.get_open_short_targets('2018-01-29')


def test_technical_selector():
    selector = TechnicalSelector(security_type=SecurityType.stock, start_timestamp='2019-01-01',
                                 end_timestamp='2019-06-10',
                                 level=TradingLevel.LEVEL_1DAY,
                                 provider=Provider.JOINQUANT)

    selector.run()

    print(selector.get_result_df())

    targets = selector.get_open_long_targets('2019-06-04')

    assert 'stock_sz_000338' not in targets
    assert 'stock_sz_000338' not in targets
    assert 'stock_sz_002572' not in targets
    assert 'stock_sz_002572' not in targets

    targets = selector.get_open_short_targets('2019-06-04')
    assert 'stock_sz_000338' in targets
    assert 'stock_sz_000338' in targets
    assert 'stock_sz_002572' in targets
    assert 'stock_sz_002572' in targets

    selector.move_on(timeout=0)

    targets = selector.get_open_long_targets('2019-06-19')

    assert 'stock_sz_000338' in targets

    assert 'stock_sz_002572' not in targets

    targets = selector.get_keep_long_targets('2019-06-19')

    assert 'stock_sz_000338' not in targets

    assert 'stock_sz_002572' not in targets
