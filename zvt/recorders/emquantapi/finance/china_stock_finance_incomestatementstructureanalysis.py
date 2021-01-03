# -*- coding: utf-8 -*-
from zvt.domain import FinanceIncomeStatementStructureAnalysis
from zvt.recorders.emquantapi.finance.base_china_stock_finance_recorder import EmBaseChinaStockFinanceRecorder
from zvt.utils.utils import add_func_to_value, first_item_to_float

finance_incomestatementstructureanalysis_map = {

    'financial_expense_rate': 'QFINAEXPENSETOGR',  # 财务费用与营业总收入之比
    'operating_profit_to_total_profit': 'QOPERATEINCOMETOEBT',  # 经营活动净收益与利润总额之比
    'net_profit_to_total_operate_revenue': 'QNITOGR',  # 净利润与营业总收入之比
    'admin_expense_rate': 'QADMINEXPENSETOGR',  # 管理费用与营业总收入之比
    'operating_profit_to_operating_revenue': 'QOPTOGR',  # 营业利润与营业总收入之比
    'total_operating_cost_to_total_operating_income': 'QGCTOGR',  # 营业总成本与营业总收入之比

    # 'R_TR': '',  # 营业收入与营业总收入之比
    # 'COGS_TR': '',  # 营业成本与营业总收入之比
    # 'BTAX_SURCHG_TR': '',  # 营业税金及附加与营业总收入之比
    # 'PERIOD_EXP_TR': '',  # 期间费用与营业总收入之比
    # 'SELL_EXP_TR': '',  # 销售费用与营业总收入之比
    # 'AIL_TR': '',  # 资产减值损失与营业总收入之比
    # 'OPA_P_TR': '',  # 经营活动净收益与营业总收入之比
    # 'VAL_CHG_P_TR': '',  # 价值变动净收益与营业总收入之比
    # 'FV_CHG_G_TR': '',  # 公允价值变动收益与营业总收入之比
    # 'INV_INC_TR': '',  # 投资收益与营业总收入之比
    # 'NOPG_TR': '',  # 营业外收入与营业总收入之比
    # 'NOPL_TR': '',  # 营业外支出与营业总收入之比
    # 'TP_TR': '',  # 利润总额与营业总收入之比
    # 'IT_TR': '',  # 所得税与营业总收入之比
    # 'EBITDA_TR': '',  # EBITDA与营业总收入之比
    # 'EBIT_TR': '',  # EBIT与营业总收入之比
    # 'VAL_CHG_P_TP': '',  # 价值变动净收益与利润总额之比
    # 'OP_TP': '',  # 营业利润与利润总额之比
    # 'N_NOPI_TP': '',  # 营业外收支净额与利润总额之比
    # 'IT_TP': '',  # 所得税与利润总额之比
    # 'NI_CUT_NI': '',  # 扣除非经常损益后的归母净利润与归母净利润之比
}
add_func_to_value(finance_incomestatementstructureanalysis_map, first_item_to_float)


class ChinaStockFinanceIncomeStatementStructureAnalysisRecorder(EmBaseChinaStockFinanceRecorder):
    """
    财务指标-利润表结构分析
    """
    data_schema = FinanceIncomeStatementStructureAnalysis

    finance_report_type = 'FinanceIncomeStatementStructureAnalysis'

    data_type = 10

    def get_data_map(self):
        return finance_incomestatementstructureanalysis_map


__all__ = ['ChinaStockFinanceIncomeStatementStructureAnalysisRecorder']

if __name__ == '__main__':
    # init_log('income_statement.log')
    recorder = ChinaStockFinanceIncomeStatementStructureAnalysisRecorder(codes=['002572'])
    recorder.run()
