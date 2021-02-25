# -*- coding: utf-8 -*-
from zvt.domain import FinanceDuPont
from zvt.recorders.emquantapi.finance.base_china_stock_finance_recorder import EmBaseChinaStockFinanceRecorder
from zvt.utils.utils import add_func_to_value, first_item_to_float

finance_dupont_map = {
    'inc_net_profit_shareholders_to_net_profit': 'DUPONTPNITONI',  # 归属母公司股东的净利润与净利润之比
    'roe_avg': 'DUPONTROE',  # 净资产收益率ROE
    'em': 'DUPONTASSETSTOEQUITY',  # 权益乘数(杜邦分析)
    'total_assets_turnover': 'DUPONTASSETTURN',  # 总资产周转率
    'net_profit_to_total_operate_revenue': 'DUPONTNITOGR',  # 净利润与营业总收入之比
    'net_profit_to_total_profits': 'DUPONTTAXBURDEN',  # 净利润与利润总额之比
    'total_profits_to_fi_ebit': 'DUPONTINTBURDEN',  # 利润总额与息税前利润之比
    'fi_ebit_to_total_op_income': 'DUPONTEBITTOGR',  # 息税前利润与营业总收入之比
    # 'ADMIN_EXP': '',  # 管理费用
    # 'AR': '',  # 应收账款
    # 'ASSET_LIAB_RATIO': '',  # 资产负债率
    # 'ASSETS_IMPAIR_LOSS': '',  # 资产减值损失
    # 'BIZ_TAX_SURCHG': '',  # 税金及附加
    # 'CASH_C_EQUIV': '',  # 货币资金
    # 'CIP': '',  # 在建工程
    # 'COGS': '',  # 营业成本
    # 'FINAN_EXP': '',  # 财务费用
    # 'FIXED_ASSETS': '',  # 固定资产
    # 'INCOME_TAX': '',  # 所得税费用
    # 'INTAN_ASSETS': '',  # 无形资产
    # 'INVENTORIES': '',  # 存货
    # 'IS_INDUSTRY': '',  # 是否一般工商业
    # 'MINORITY_ASSET': '',  # 少数股东权益占总资产比重(平均)
    # 'MINORITY_INT': '',  # 少数股东权益
    # 'MINORITY_INT_A': '',  # 平均少数股东权益
    # 'MINORITY_INT_BGN': '',  # 年初少数股东权益
    # 'NOPERATE_PROFIT': '',  # 营业外收支
    # 'NP_MARGIN': '',  # 销售净利率
    # 'OTH_EQUITY_INSTR': '',  # 其他权益工具
    # 'PERIOD_EXP': '',  # 期间费用
    # 'PREPAYMENT': '',  # 预付款项
    # 'REVENUE': '',  # 营业收入
    # 'ROA': '',  # 总资产收益率(平均)
    # 'SELL_EXP': '',  # 销售费用
    # 'T_ASSETS': '',  # 总资产
    # 'T_ASSETS_A': '',  # 平均总资产
    # 'T_ASSETS_BGN': '',  # 年初总资产
    # 'T_CA': '',  # 流动资产
    # 'T_COGS': '',  # 营业总成本
    # 'T_LIAB': '',  # 总负债
    # 'T_LIAB_A': '',  # 平均总负债
    # 'T_LIAB_BGN': '',  # 年初总负债
    # 'T_NCA': '',  # 非流动资产
    # 'T_REVENUE': '',  # 营业总收入
    # 'VAL_CHG_PROFIT': '',  # 价值变动净收益

}
add_func_to_value(finance_dupont_map, first_item_to_float)


class ChinaStockFinanceDuPontRecorder(EmBaseChinaStockFinanceRecorder):
    """
    财务指标-杜邦分析
    """
    data_schema = FinanceDuPont

    finance_report_type = 'FinanceDuPont'

    data_type = 11

    def get_data_map(self):
        return finance_dupont_map


__all__ = ['ChinaStockFinanceDuPontRecorder']

if __name__ == '__main__':
    # init_log('income_statement.log')
    recorder = ChinaStockFinanceDuPontRecorder(codes=['002572'])
    recorder.run()
