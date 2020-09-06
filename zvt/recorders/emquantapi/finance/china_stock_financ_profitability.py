# -*- coding: utf-8 -*-
from zvt.domain import FinanceProfitAbility
from zvt.recorders.emquantapi.finance.base_china_stock_finance_recorder import EmBaseChinaStockFinanceRecorder
from zvt.utils.utils import add_func_to_value, first_item_to_float

financial_indicators_profitability_map = {
    # 更新时间
    "report_date": "REPORTDATE",
    'gross_income_ratio': 'GPMARGIN',  # 销售毛利率
    'net_profit_ratio': 'NPMARGIN',  # 销售净利率
    'roe_diluted': 'ROEDILUTED',  # 净资产收益率ROE(摊薄)
    'roe_avg': 'ROEAVG',  # 净资产收益率ROE(平均)
    'roe_wa': 'ROEWA',  # 净资产收益率ROE(加权)
    'roe_ex_diluted': 'ROEEXDILUTED',  # 净资产收益率ROE(扣除/摊薄)
    'roe_ex_wa': 'ROEEXWA',  # 净资产收益率ROE(扣除/加权)
    'net_roa': 'NROA',  # 总资产净利率ROA
    'roa': 'ROA',  # 总资产报酬率ROA
    'roic': 'ROIC'  # 投入资本回报率ROIC
}

add_func_to_value(financial_indicators_profitability_map, first_item_to_float)


class ChinaStockFinanceProfitAbilityRecorder(EmBaseChinaStockFinanceRecorder):
    """
    财务指标-盈利能力
    """
    data_schema = FinanceProfitAbility

    finance_report_type = 'FinanceProfitAbility'

    data_type = 6

    def get_data_map(self):
        return financial_indicators_profitability_map


__all__ = ['ChinaStockFinanceProfitAbilityRecorder']

if __name__ == '__main__':
    # init_log('income_statement.log')
    recorder = ChinaStockFinanceProfitAbilityRecorder(codes=['002572'])
    recorder.run()
