# -*- coding: utf-8 -*-
from zvt.contract import IntervalLevel, AdjustType
from zvt.recorders.em import em_api

import requests


def test_get_kdata():
    # 上证A股
    session = requests.Session()
    df = em_api.get_kdata(
        session=session,
        entity_id="stock_sh_601318",
        level=IntervalLevel.LEVEL_1DAY,
        adjust_type=AdjustType.qfq,
        limit=5,
    )
    print(df)
    df = em_api.get_kdata(
        session=session,
        entity_id="stock_sh_601318",
        level=IntervalLevel.LEVEL_1DAY,
        adjust_type=AdjustType.hfq,
        limit=5,
    )
    print(df)
    df = em_api.get_kdata(
        session=session,
        entity_id="stock_sh_601318",
        level=IntervalLevel.LEVEL_1DAY,
        adjust_type=AdjustType.bfq,
        limit=5,
    )
    print(df)
    # 深圳A股
    df = em_api.get_kdata(
        session=session,
        entity_id="stock_sz_000338",
        level=IntervalLevel.LEVEL_1DAY,
        adjust_type=AdjustType.qfq,
        limit=5,
    )
    print(df)
    df = em_api.get_kdata(
        session=session,
        entity_id="stock_sz_000338",
        level=IntervalLevel.LEVEL_1DAY,
        adjust_type=AdjustType.hfq,
        limit=5,
    )
    print(df)
    df = em_api.get_kdata(
        session=session,
        entity_id="stock_sz_000338",
        level=IntervalLevel.LEVEL_1DAY,
        adjust_type=AdjustType.bfq,
        limit=5,
    )
    print(df)
