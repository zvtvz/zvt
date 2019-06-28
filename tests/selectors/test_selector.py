# -*- coding: utf-8 -*-
from zvt.selectors.examples.technical_selector import TechnicalSelector
from zvt.utils.pd_utils import df_is_not_null
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

    targets = selector.get_targets('2019-06-04')
    if df_is_not_null(targets):
        assert 'stock_sz_000338' not in targets['security_id'].tolist()
        assert 'stock_sz_000338' not in targets['security_id'].tolist()
        assert 'stock_sz_002572' not in targets['security_id'].tolist()
        assert 'stock_sz_002572' not in targets['security_id'].tolist()

    selector.move_on(timeout=0)

    targets = selector.get_targets('2019-06-19')
    if df_is_not_null(targets):
        assert 'stock_sz_000338' in targets['security_id'].tolist()

        assert 'stock_sz_002572' not in targets['security_id'].tolist()
