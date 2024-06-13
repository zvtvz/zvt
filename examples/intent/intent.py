# -*- coding: utf-8 -*-
from zvt.api.intent import compare
from zvt.domain import Indexus1dKdata, Index, Indexus, Index1dKdata, Currency1dKdata
from zvt.domain import TreasuryYield


def china_vs_us_stock():
    # 上证，道琼斯指数
    Index.record_data()
    Indexus.record_data()
    Index1dKdata.record_data(entity_id="index_sh_000001")
    Indexus1dKdata.record_data(entity_id="indexus_us_SPX")
    compare(entity_ids=["index_sh_000001", "indexus_us_SPX"], start_timestamp="2000-01-01", scale_value=100)


def us_yield_and_stock():
    # 美债收益率，道琼斯指数
    entity_ids = ["country_galaxy_US", "indexus_us_SPX"]
    compare(
        entity_ids=entity_ids,
        start_timestamp="1990-01-01",
        scale_value=None,
        schema_map_columns={TreasuryYield: ["yield_2", "yield_5"], Indexus1dKdata: ["close"]},
    )


def commodity_and_stock():
    # 江西铜业，沪铜
    entity_ids = ["stock_sh_600362", "future_shfe_CU"]
    compare(
        entity_ids=entity_ids,
        start_timestamp="2005-01-01",
        scale_value=100,
    )


def compare_metal():
    # 沪铜,沪铝,螺纹钢
    entity_ids = ["future_shfe_CU", "future_shfe_AL", "future_shfe_RB"]
    compare(
        entity_ids=entity_ids,
        start_timestamp="2009-04-01",
        scale_value=100,
    )


def compare_udi_and_stock():
    # 美股指数
    # Indexus.record_data()
    entity_ids = ["indexus_us_NDX", "indexus_us_SPX", "indexus_us_UDI"]
    # Indexus1dKdata.record_data(entity_ids=entity_ids, sleeping_time=0)
    compare(
        entity_ids=entity_ids,
        start_timestamp="2015-01-01",
        scale_value=100,
        schema_map_columns={Indexus1dKdata: ["close"]},
    )


def compare_cny_and_stock():
    Currency1dKdata.record_data(entity_id="currency_forex_USDCNYC")
    entity_ids = ["index_sh_000001", "currency_forex_USDCNYC"]
    compare(
        entity_ids=entity_ids,
        start_timestamp="2005-01-01",
        scale_value=100,
        schema_map_columns={Currency1dKdata: ["close"], Index1dKdata: ["close"]},
    )


if __name__ == "__main__":
    # compare_kline()
    # us_yield_and_stock()
    # commodity_and_stock()
    # compare_metal()
    # compare_udi_and_stock()
    compare_cny_and_stock()
