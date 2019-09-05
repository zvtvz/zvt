# -*- coding: utf-8 -*-
from zvt.api.quote import get_indices
from zvt.domain import StockCategory


def test_get_indices():
    df = get_indices(provider='sina', block_category=StockCategory.industry)
    print(df)

    df = get_indices(provider='eastmoney', block_category=StockCategory.industry)
    print(df)
