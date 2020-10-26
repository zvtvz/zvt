# -*- coding: utf-8 -*-
from zvt.domain import FinancePerShare
from zvt.recorders.emquantapi.finance.base_china_stock_finance_recorder import EmBaseChinaStockFinanceRecorder
from zvt.utils.utils import add_func_to_value, first_item_to_float

finance_per_share_map = {
    # 更新时间
    "report_date": "REPORTDATE",
    'eps_diluted_end': 'EPSDILUTEDEND',  # 每股收益(期末摊薄)
    'eps': 'EPSBASIC',  # 基本每股收益
    'diluted_eps': 'EPSDILUTED',  # 稀释每股收益
    'bps': 'BPS',  # 每股净资产
    'total_operating_revenue_ps': 'GRPS',  # 每股营业总收入
    'operating_revenue_pee': 'ORPS',  # 每股营业收入
    # 'operating_profit_ps': '',  # 每股营业利润
    'earnings_bf_interest_taxes_ps': 'EBITPS',  # 每股息税前利润
    'capital_reserve_ps': 'CAPITALRESERVEPS',  # 每股资本公积
    'surplus_reserve_fund_ps': 'SURPLUSRESERVEPS',  # 每股盈余公积

    'undistributed_profit_ps': 'UNDISTRIBUTEDPS',  # 每股未分配利润
    'retained_earnings_ps': 'RETAINEDPS',  # 每股留存收益
    'net_operate_cash_flow_ps': 'CFOPS',  # 每股经营活动产生的现金流量净额
    'net_cash_flow_ps': 'CFPS',  # 每股现金流量净额
    'free_cash_flow_firm_ps': 'FCFFPS',  # 每股企业自由现金流量
    'free_cash_flow_equity_ps': 'FCFEPS',  # 每股股东自由现金流量
    # 'RESER_PS': '',  # 每股公积金
}

add_func_to_value(finance_per_share_map, first_item_to_float)


class ChinaStockFinancePerShareRecorder(EmBaseChinaStockFinanceRecorder):
    data_schema = FinancePerShare

    finance_report_type = 'FinancePerShare'

    data_type = 7

    def get_data_map(self):
        return finance_per_share_map


__all__ = ['ChinaStockFinancePerShareRecorder']

if __name__ == '__main__':
    # init_log('income_statement.log')
    recorder = ChinaStockFinancePerShareRecorder(codes=['002572'])
    recorder.run()
