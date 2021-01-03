# -*- coding: utf-8 -*-
from zvt.domain import FinanceCapitalStructure

from zvt.recorders.emquantapi.finance.base_china_stock_finance_recorder import EmBaseChinaStockFinanceRecorder
from zvt.utils.utils import add_func_to_value, first_item_to_float

capital_structure_map = {

    'debt_asset_ratio': 'LIBILITYTOASSET',  # 资产负债率
    'em': 'ASSETSTOEQUITY',  # 权益乘数
    'ca_to_asset': 'CATOASSET',  # 流动资产/总资产
    'nc_to_asset': 'NCATOASSET',  # 非流动资产/总资产
    'tangible_assets_to_asset': 'TANGIBLEASSETSTOASSET',  # 有形资产/总资产
    'equity_to_total_capital': 'EQUITYTOTOTALCAPITAL',  # 归属母公司股东的权益/全部投入资本
    'interest_liblity_to_total_capital': 'INTERESTLIBILITYTOTOTALCAPITAL',  # 带息负债/全部投入资本
    'cl_to_libility': 'CLTOLIBILITY',  # 流动负债/负债合计
    'cnl_to_libility': 'NCLTOLIBILITY',  # 非流动负债/负债合计
    'interest_liblity_to_libility': 'INTERESLIBILITYTOLIBILITY',  # 有息负债率

}
add_func_to_value(capital_structure_map, first_item_to_float)


class ChinaStockFinanceCapitalStructure(EmBaseChinaStockFinanceRecorder):
    """
    财务指标-资本结构
    """
    data_schema = FinanceCapitalStructure

    finance_report_type = 'FinanceCapitalStructure'

    data_type = 16

    def get_data_map(self):
        return capital_structure_map


__all__ = ['ChinaStockFinanceCapitalStructure']

if __name__ == '__main__':
    # init_log('income_statement.log')
    recorder = ChinaStockFinanceCapitalStructure(codes=['002572'])
    recorder.run()
