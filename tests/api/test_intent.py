# -*- coding: utf-8 -*-
from zvt.api.intent import compare_entity, distribute_entity, composite_entity, composite_all
from zvt.contract.drawer import ChartType
from zvt.domain import FinanceFactor, CashFlowStatement, BalanceSheet, Stock1dKdata
from zvt.utils import to_pd_timestamp


def test_compare_kdata():
    entity_ids = ["stock_sz_000338", "stock_sh_601318"]
    compare_entity(entity_ids=entity_ids)


def test_compare_line():
    entity_ids = ["stock_sz_000338", "stock_sh_601318"]
    compare_entity(entity_ids=entity_ids, schema_map_columns={FinanceFactor: [FinanceFactor.roe]})


def test_compare_scatter():
    entity_ids = ["stock_sz_000338", "stock_sh_601318"]
    compare_entity(
        entity_ids=entity_ids, schema_map_columns={FinanceFactor: [FinanceFactor.roe]}, chart_type=ChartType.scatter
    )


def test_compare_area():
    entity_ids = ["stock_sz_000338", "stock_sh_601318"]
    compare_entity(
        entity_ids=entity_ids, schema_map_columns={FinanceFactor: [FinanceFactor.roe]}, chart_type=ChartType.area
    )


def test_compare_bar():
    entity_ids = ["stock_sz_000338", "stock_sh_601318"]
    compare_entity(
        entity_ids=entity_ids, schema_map_columns={FinanceFactor: [FinanceFactor.roe]}, chart_type=ChartType.bar
    )


def test_distribute():
    distribute_entity(entity_ids=None, data_schema=FinanceFactor, columns=["roe"])


def test_composite():
    composite_entity(
        entity_id="stock_sz_000338",
        data_schema=CashFlowStatement,
        columns=[
            CashFlowStatement.net_op_cash_flows,
            CashFlowStatement.net_investing_cash_flows,
            CashFlowStatement.net_financing_cash_flows,
        ],
        filters=[
            CashFlowStatement.report_period == "year",
            CashFlowStatement.report_date == to_pd_timestamp("2016-12-31"),
        ],
    )
    composite_entity(
        entity_id="stock_sz_000338",
        data_schema=BalanceSheet,
        columns=[
            BalanceSheet.total_current_assets,
            BalanceSheet.total_non_current_assets,
            BalanceSheet.total_current_liabilities,
            BalanceSheet.total_non_current_liabilities,
        ],
        filters=[BalanceSheet.report_period == "year", BalanceSheet.report_date == to_pd_timestamp("2016-12-31")],
    )


def test_composite_all():
    composite_all(
        entity_ids=None, data_schema=Stock1dKdata, column=Stock1dKdata.turnover, timestamp=to_pd_timestamp("2016-12-02")
    )
