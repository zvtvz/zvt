# -*- coding: utf-8 -*-

from zvt.domain import FinanceFactor, SecurityType, TradingLevel
from zvt.factors.factor import OneSchemaScoreFactor


class FinanceGrowthFactor(OneSchemaScoreFactor):
    def __init__(self, security_list=None, security_type=SecurityType.stock, exchanges=['sh', 'sz'], codes=None,
                 the_timestamp=None, start_timestamp=None, end_timestamp=None, keep_all_timestamp=True,
                 fill_method='ffill',
                 columns=[FinanceFactor.op_income_growth_yoy, FinanceFactor.net_profit_growth_yoy, FinanceFactor.rota,
                          FinanceFactor.roe], filters=None, provider='eastmoney', level=TradingLevel.LEVEL_1DAY,
                 effective_number=None, depth_computing_method='ma',
                 depth_computing_param={'window': '365D', 'on': 'timestamp'}, breadth_computing_method='quantile',
                 breadth_computing_param={'score_levels': [0.1, 0.3, 0.5, 0.7, 0.9]}) -> None:
        super().__init__(FinanceFactor, security_list, security_type, exchanges, codes, the_timestamp, start_timestamp,
                         end_timestamp, keep_all_timestamp, fill_method, columns, filters, provider, level,
                         effective_number, depth_computing_method, depth_computing_param, breadth_computing_method,
                         breadth_computing_param)


if __name__ == '__main__':
    factor = FinanceGrowthFactor(start_timestamp='2017-01-01',
                                 end_timestamp='2018-12-31')
    factor.run()

    print(factor.get_df())
