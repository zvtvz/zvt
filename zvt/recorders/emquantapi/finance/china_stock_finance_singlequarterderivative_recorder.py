# -*- coding: utf-8 -*-
from zvt.domain import FinanceSinglEquarterDerivative
from zvt.recorders.emquantapi.finance.base_china_stock_finance_recorder import EmBaseChinaStockFinanceRecorder
from zvt.utils.utils import add_func_to_value, first_item_to_float

finance_singlequarterderivative_map = {
    # 更新时间
    'fi_investment_income': 'INVESTINCOME',  # 价值变动净收益
    'fi_gross_margin': 'GROSSMARGIN',  # 毛利
    'deducted_net_profit': 'DEDUCTEDINCOME',  # 扣除非经常性损益后的净利润
    'fi_extraordinary_item': 'EXTRAORDINARY',  # 非经常性损益
    'fi_operate_income': 'OPERATEINCOME',  # 经营活动净收益
}
add_func_to_value(finance_singlequarterderivative_map, first_item_to_float)


class ChinaStockFinanceSinglEquarterDerivativeRecorder(EmBaseChinaStockFinanceRecorder):
    """
    财务指标-单季财务衍生数据
    """
    data_schema = FinanceSinglEquarterDerivative

    finance_report_type = 'FinanceSinglEquarterDerivative'

    data_type = 11

    def get_data_map(self):
        return finance_singlequarterderivative_map


__all__ = ['ChinaStockFinanceSinglEquarterDerivativeRecorder']

if __name__ == '__main__':
    # init_log('income_statement.log')
    recorder = ChinaStockFinanceSinglEquarterDerivativeRecorder(codes=['002572'])
    recorder.run()
