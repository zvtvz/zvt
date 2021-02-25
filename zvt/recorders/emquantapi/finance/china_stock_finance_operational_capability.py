# -*- coding: utf-8 -*-
from zvt.domain import FinanceOperationalCapability
from zvt.recorders.emquantapi.finance.base_china_stock_finance_recorder import EmBaseChinaStockFinanceRecorder
from zvt.utils.utils import add_func_to_value, first_item_to_float

financial_operational_capability_map = {

    'fixed_assets_turnover_rate': 'FATURNRATIO',  # 固定资产周转率
    'current_asset_turnover_rate': 'CATURNRATIO',  # 流动资产周转率
    'total_assets_turnover': 'ASSETTURNRATIO',  # 总资产周转率
    'inventory_turnover': 'INVTURNRATIO',  # 存货周转率
    'inventory_turnover_days': 'INVTURNDAYS',  # 存货周转天数
    'receivables_turnover': 'ARTURNRATIO',  # 应收账款周转率(含应收票据)
    'receivables_turnover_days': 'ARTURNDAYS',  # 应收账款周转天数(含应收票据)
    'operating_cycle': 'TURNDAYS',  # 营业周期
    # 'accounts_payable_turnover_rate': 'ACCOUNTSTURNOVERRATIO',  # 应付账款周转率
    'accounts_payable_turnover_days': 'APTURNDAYS',  # 应付账款周转天数(含应付票据)
}

add_func_to_value(financial_operational_capability_map, first_item_to_float)


class ChinaStockFinanceOperationalCapabilityRecorder(EmBaseChinaStockFinanceRecorder):
    """
    财务指标-盈利能力
    """
    data_schema = FinanceOperationalCapability
    finance_report_type = 'FinanceOperationalCapability'

    data_type = 6

    def get_data_map(self):
        return financial_operational_capability_map


__all__ = ['ChinaStockFinanceOperationalCapabilityRecorder']

if __name__ == '__main__':
    # init_log('income_statement.log')
    recorder = ChinaStockFinanceOperationalCapabilityRecorder(codes=['002572'])
    recorder.run()
