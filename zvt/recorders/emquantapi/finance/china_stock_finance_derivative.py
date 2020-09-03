# -*- coding: utf-8 -*-
from zvt.domain import FinanceDerivative
from zvt.recorders.emquantapi.finance.base_china_stock_finance_recorder import EmBaseChinaStockFinanceRecorder
from zvt.utils.utils import add_func_to_value, first_item_to_float

finance_derivative_map = {
    # 更新时间
    "report_date": "REPORTDATE",

    'fi_interest_free_current_liabilities': 'EXINTERESTCL',  # 无息流动负债
    'fi_interest_free_non_current_liabilities': 'EXINTERESTNCL',  # 无息非流动负债

    'fi_interest_bearing_debt': 'INTERESTLIBILITY',  # 带息债务
    'fi_net_debt': 'NETLIBILITY',  # 净债务
    'fi_tangible_net_assets': 'TANGIBLEASSET',  # 有形净资产
    'fi_working_capital': 'WORKINGCAPITAL',  # 营运资本
    'fi_net_working_apital': 'NETWORKINGCAPITAL',  # 净营运资本

    'fi_retained_earnings': 'RETAINED',  # 留存收益
    'fi_gross_margin': 'GROSSMARGIN',  # 毛利
    'fi_operate_income': 'OPERATEINCOME',  # 经营活动净收益
    'fi_investment_income': 'INVESTINCOME',  # 价值变动净收益

    'fi_ebit': 'EBIT',  # 息税前利润
    'fi_ebitda': 'EBITDA',  # 息税折旧摊销前利润

    'fi_extraordinary_item': 'EXTRAORDINARY',  # 非经常性损益
    'fi_deducted_income': 'DEDUCTEDINCOME',  # 扣除非经常性损益后的归属于上市公司股东的净利润
    'fi_free_cash_flow_firm': 'FCFF',  # 企业自由现金流量
    'fi_free_cash_flow_equity': 'FCFE',  # 股权自由现金流量
    'fi_depreciation_amortization': 'DA',  # 折旧与摊销
    # 'EBIAT':'',#息前税后利润
    # 'N_INT_EXP':'',#净利息费用
    # 'INT_CL':'',#带息流动负债
    # 'IC':'',#投入资本
}

add_func_to_value(finance_derivative_map, first_item_to_float)


class ChinaStockFinanceDerivativeRecorder(EmBaseChinaStockFinanceRecorder):
    """
    财务衍生数据
    """
    data_schema = FinanceDerivative

    finance_report_type = 'FinanceDerivative'

    data_type = 5

    def get_data_map(self):
        return finance_derivative_map


__all__ = ['ChinaStockFinanceDerivativeRecorder']

if __name__ == '__main__':
    # init_log('income_statement.log')
    recorder = ChinaStockFinanceDerivativeRecorder(codes=['002572'])
    recorder.run()
