# -*- coding: utf-8 -*-
from typing import List, Union

import pandas as pd

from zvt.domain import FinanceFactor, SecurityType, TradingLevel, Provider
from zvt.factors.factor import ScoreFactor


class FinanceGrowthFactor(ScoreFactor):

    def __init__(self,
                 security_list: List[str] = None,
                 security_type: Union[str, SecurityType] = SecurityType.stock,
                 exchanges: List[str] = ['sh', 'sz'],
                 codes: List[str] = None,
                 the_timestamp: Union[str, pd.Timestamp] = None,
                 start_timestamp: Union[str, pd.Timestamp] = None,
                 end_timestamp: Union[str, pd.Timestamp] = None,
                 columns: List = [FinanceFactor.op_income_growth_yoy, FinanceFactor.net_profit_growth_yoy,
                                  FinanceFactor.rota,
                                  FinanceFactor.roe],
                 filters: List = None,
                 provider: Union[str, Provider] = 'eastmoney',
                 level: TradingLevel = TradingLevel.LEVEL_1DAY,
                 real_time: bool = False,
                 refresh_interval: int = 10,
                 category_field: str = 'security_id',
                 keep_all_timestamp: bool = True,
                 fill_method: str = 'ffill',
                 effective_number: int = None,
                 depth_computing_method='ma',
                 depth_computing_param={'window': '365D', 'on': 'timestamp'},
                 breadth_computing_method='quantile',
                 breadth_computing_param={'score_levels': [0.1, 0.3, 0.5, 0.7, 0.9]}) -> None:
        super().__init__(FinanceFactor, security_list, security_type, exchanges, codes, the_timestamp, start_timestamp,
                         end_timestamp, columns, filters, provider, level, real_time, refresh_interval, category_field,
                         keep_all_timestamp, fill_method, effective_number, depth_computing_method,
                         depth_computing_param, breadth_computing_method, breadth_computing_param)


if __name__ == '__main__':
    factor = FinanceGrowthFactor(start_timestamp='2018-01-01',
                                 end_timestamp='2018-12-31',
                                 codes=['000338', '000778', '601318'])

    factor.draw_result(value_fields=['op_income_growth_yoy', 'rota'])
