# -*- coding: utf-8 -*-
from zvt.domain import FinanceGrowthAbility
from zvt.recorders.emquantapi.finance.base_china_stock_finance_recorder import EmBaseChinaStockFinanceRecorder
from zvt.utils.utils import add_func_to_value, first_item_to_float

financial_growth_ability_map = {

    'total_op_income_growth_yoy': 'YOYGR',  # 营业总收入同比增长率
    'op_income_growth_yoy': 'YOYOR',  # 营业收入同比增长率
    'op_profit_growth_yoy': 'YOYOP',  # 营业利润同比增长率
    'total_profit_growth_yoy': 'YOYEBT',  # 利润总额同比增长率
    'net_profit_growth_yoy': 'YOYNI',  # 净利润同比增长率
    'inc_net_profit_shareholders_yoy': 'YOYPNI',  # 归属母公司股东的净利润同比增长率
    'inc_net_profit_shareholders_deducted_yoy': 'YOYPNIDEDUCTED',  # 归属母公司股东的净利润同比增长率(扣除非经常性损益)
    'basic_eps_you': 'YOYEPSBASIC',  # 基本每股收益同比增长率
    'diluted_eps_yoy': 'YOYEPSDILUTED',  # 稀释每股收益同比增长率
    'roe_liluted_yoy': 'YOYROELILUTED',  # 净资产收益率同比增长率(摊薄)
    'net_op_cash_flows_yoy': 'YOYCFO',  # 经营活动产生的现金流量净额同比增长率
    'net_operate_cash_flow_ps_yoy': 'YOYCFOPS',  # 每股经营活动中产生的现金流量净额同比增长率
    'total_assets_relative_of_year': 'ASSETRELATIVE',  # 资产总计相对年初增长率
    'equity_relative_of_year': 'EQUITYRELATIVE',  # 归属母公司股东的权益相对年初增长率
    'bps_relativeof_year': 'BPSRELATIVE',  # 每股净资产相对年初增长率
}
add_func_to_value(financial_growth_ability_map, first_item_to_float)


class ChinaStockFinanceGrowthAbilityRecorder(EmBaseChinaStockFinanceRecorder):
    """
    财务指标-成长能力
    """
    data_schema = FinanceGrowthAbility

    finance_report_type = 'FinanceGrowthAbility'

    data_type = 5

    def get_data_map(self):
        return financial_growth_ability_map


__all__ = ['ChinaStockFinanceGrowthAbilityRecorder']

if __name__ == '__main__':
    # init_log('income_statement.log')
    recorder = ChinaStockFinanceGrowthAbilityRecorder(codes=['002572'])
    recorder.run()
