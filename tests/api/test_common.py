# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-
from zvdata import IntervalLevel
from zvt.api import get_kdata
from zvt.api.common import to_high_level_kdata
from ..context import init_test_context

init_test_context()


def test_to_high_level_kdata():
    day_df = get_kdata(provider='joinquant', level=IntervalLevel.LEVEL_1DAY, entity_id='stock_sz_000338')
    print(day_df)

    df = to_high_level_kdata(kdata_df=day_df.loc[:'2019-09-01', :], to_level=IntervalLevel.LEVEL_1WEEK)

    print(df)
