# -*- coding: utf-8 -*-
from zvt.domain import FinanceBalanceSheetStructureAnalysis
from zvt.recorders.emquantapi.finance.base_china_stock_finance_recorder import EmBaseChinaStockFinanceRecorder
from zvt.utils.utils import add_func_to_value, first_item_to_float

financial_balancesheetstructureanalysis_map = {
    # 更新时间
    "report_date": "REPORTDATE",
    'cfo_to_gr': 'CFOTOGR',  #经营活动产生的现金流量净额/营业总收入
    'sales_cash_intoor': 'SALESCASHINTOOR',  # 销售商品提供劳务收到的现金/营业收入
    'qcfi_to_cf': 'QCFITOCF',  # 投资活动产生的现金流量净额占比
    'qcfo_to_cfo': 'QCFOTCFO',  # 经营活动产生的现金流量净额占比
    'qcfo_to_or': 'QCFOTOOR',  # 经营活动产生的现金流量净额/营业收入
    'qcfo_to_operate_income': 'QCFOTOOPERATEINCOME',  # 经营活动产生的现金流量净额/经营活动净收益
    'qcff_to_cf': 'QCFFTOCF',  # 筹资活动产生的现金流量净额占比
    # 'ADV_R_R': '',  # 预收款项/营业收入
    # 'AR_R': '',  # 应收账款/营业收入
    # 'P_FIXA_O_DA': '',  # 投资支出/折旧和摊销
    # 'C_RCVRY_A': '',  # 全部资产现金回收率
    # 'N_CF_OPA_OP': '',  # 经营活动产生的现金流量净额/营业利润
}
add_func_to_value(financial_balancesheetstructureanalysis_map, first_item_to_float)


class ChinaStockFinanceBalanceSheetStructureAnalysisRecorder(EmBaseChinaStockFinanceRecorder):
    """
    财务指标-资产负债表结构分析
    """
    data_schema = FinanceBalanceSheetStructureAnalysis

    finance_report_type = 'FinanceBalanceSheetStructureAnalysis'

    data_type = 10

    def get_data_map(self):
        return financial_balancesheetstructureanalysis_map


__all__ = ['ChinaStockFinanceBalanceSheetStructureAnalysisRecorder']

if __name__ == '__main__':
    # init_log('income_statement.log')
    recorder = ChinaStockFinanceBalanceSheetStructureAnalysisRecorder(codes=['002572'])
    recorder.run()
