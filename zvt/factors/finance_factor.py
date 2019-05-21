# -*- coding: utf-8 -*-
import pandas as pd

from zvt.domain import FinanceFactor, SecurityType
from zvt.factors.factor import OneSchemaScoreFactor


class FinanceGrowthFactor(OneSchemaScoreFactor):
    data_schema = FinanceFactor

    def __init__(self, security_type=SecurityType.stock, exchanges=['sh', 'sz'], codes=None, the_timestamp=None,
                 window=None, window_func='mean', start_timestamp=None, end_timestamp=None, keep_all_timestamp=True,
                 fill_method='ffill', columns=[FinanceFactor.op_income_growth_yoy, FinanceFactor.net_profit_growth_yoy],
                 filters=None, provider='eastmoney',
                 score_levels=[0.1, 0.3, 0.5, 0.7, 0.9]) -> None:
        super().__init__(security_type, exchanges, codes, the_timestamp, window, window_func, start_timestamp,
                         end_timestamp, keep_all_timestamp, fill_method, columns, filters, provider, score_levels)


if __name__ == '__main__':
    factor = FinanceGrowthFactor(window=pd.DateOffset(days=365), start_timestamp='2010-01-01',
                                 end_timestamp='2018-12-31')
    factor.run()

    print(factor.get_df())
