# -*- coding: utf-8 -*-
from zvdata.normal_data import NormalData
from zvt.api import get_kdata
from zvt.factors import MaTransformer, MacdTransformer


def test_ma_transformer():
    df = get_kdata(entity_id='stock_sz_000338', start_timestamp='2019-01-01', provider='joinquant')
    df = NormalData(df=df).data_df

    t = MaTransformer(windows=[5, 10])

    result_df = t.transform(df=df)

    print(result_df)


def test_MacdTransformer():
    df = get_kdata(entity_id='stock_sz_000338', start_timestamp='2019-01-01', provider='joinquant')
    df = NormalData(df=df).data_df

    t = MacdTransformer()

    result_df = t.transform(df=df)

    print(result_df)
