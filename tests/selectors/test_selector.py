# -*- coding: utf-8 -*-
from zvt.selectors.zvt_selector import TechnicalSelector
from ..context import init_context

init_context()

from zvt.domain import SecurityType, TradingLevel, Provider


def test_technical_selector():
    selector = TechnicalSelector(security_type=SecurityType.stock, start_timestamp='2019-01-01',
                                 end_timestamp='2019-06-10',
                                 level=TradingLevel.LEVEL_1DAY,
                                 provider=Provider.JOINQUANT)

    selector.run()

    print(selector.get_result_df())

    assert 'stock_sz_000338' in selector.get_targets('2019-06-04')['security_id'].tolist()
    assert 'stock_sz_000338' in selector.get_targets('2019-06-04')['security_id'].tolist()
    assert 'stock_sz_002572' not in selector.get_targets('2019-06-04')['security_id'].tolist()
    assert 'stock_sz_002572' not in selector.get_targets('2019-06-04')['security_id'].tolist()

    selector.move_on(timeout=0)

    assert 'stock_sz_000338' in selector.get_targets('2019-06-17')['security_id'].tolist()

    assert 'stock_sz_002572' in selector.get_targets('2019-06-17')['security_id'].tolist()
