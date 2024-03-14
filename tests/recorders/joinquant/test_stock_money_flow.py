# -*- coding: utf-8 -*-
from zvt.domain import StockMoneyFlow, Stock


def test_stock_money_flow():
    provider = "joinquant"
    # Stock.record_data(provider=provider)
    StockMoneyFlow.record_data(
        codes=["300999", "688981"], provider=provider, start_timestamp="2020-12-14", compute_index_money_flow=False
    )

    data_samples = [
        {
            "id": "stock_sz_300999_2020-12-14",
            "timestamp": "2020-12-14",
            "code": "300999",
            "net_main_inflows": 46378.96 * 10000,
            "net_main_inflow_rate": 9.3 / 100,
            "net_huge_inflows": 50111.54 * 10000,
            "net_huge_inflow_rate": 10.04 / 100,
            "net_big_inflows": -3732.58 * 10000,
            "net_big_inflow_rate": -0.75 / 100,
            "net_medium_inflows": -23493.71 * 10000,
            "net_medium_inflow_rate": -4.71 / 100,
            "net_small_inflows": -22885.25 * 10000,
            "net_small_inflow_rate": -4.59 / 100,
        },
        {
            "id": "stock_sh_688981_2020-12-14",
            "timestamp": "2020-12-14",
            "code": "688981",
            "net_main_inflows": -14523.55 * 10000,
            "net_main_inflow_rate": -10.77 / 100,
            "net_huge_inflows": -17053.72 * 10000,
            "net_huge_inflow_rate": -12.65 / 100,
            "net_big_inflows": 2530.17 * 10000,
            "net_big_inflow_rate": 1.88 / 100,
            "net_medium_inflows": 6945.23 * 10000,
            "net_medium_inflow_rate": 5.15 / 100,
            "net_small_inflows": 7578.32 * 10000,
            "net_small_inflow_rate": 5.62 / 100,
        },
    ]
    StockMoneyFlow.test_data_correctness(provider=provider, data_samples=data_samples)
