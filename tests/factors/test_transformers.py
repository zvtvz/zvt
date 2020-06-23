# -*- coding: utf-8 -*-
from zvt.api.quote import get_kdata
from zvt.factors.algorithm import MaTransformer, MacdTransformer


def test_ma_transformer():
    df = get_kdata(entity_id='stock_sz_000338', start_timestamp='2019-01-01', provider='joinquant')

    t = MaTransformer(windows=[5, 10])

    result_df = t.transform(df)

    print(result_df)


def test_MacdTransformer():
    df = get_kdata(entity_id='stock_sz_000338', start_timestamp='2019-01-01', provider='joinquant')

    t = MacdTransformer()

    result_df = t.transform(df)

    print(result_df)
