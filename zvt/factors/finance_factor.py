# -*- coding: utf-8 -*-
from typing import List, Union

import pandas as pd

from zvdata.factor import ScoreFactor
from zvdata.structs import IntervalLevel
from zvt.domain import FinanceFactor


class FinanceGrowthFactor(ScoreFactor):

    def __init__(self,
                 entity_ids: List[str] = None,
                 entity_type: str = 'stock',
                 exchanges: List[str] = ['sh', 'sz'],
                 codes: List[str] = None,
                 the_timestamp: Union[str, pd.Timestamp] = None,
                 start_timestamp: Union[str, pd.Timestamp] = None,
                 end_timestamp: Union[str, pd.Timestamp] = None,
                 columns: List = [FinanceFactor.op_income_growth_yoy, FinanceFactor.net_profit_growth_yoy,
                                  FinanceFactor.rota,
                                  FinanceFactor.roe],
                 filters: List = None,
                 order: object = None,
                 limit: int = None,
                 provider: str = 'eastmoney',
                 level: Union[str, IntervalLevel] = IntervalLevel.LEVEL_1DAY,

                 category_field: str = 'entity_id',
                 time_field: str = 'report_date',
                 trip_timestamp: bool = True,
                 auto_load: bool = True,
                 keep_all_timestamp: bool = False,
                 fill_method: str = 'ffill',
                 effective_number: int = 10,
                 depth_computing_method='ma',
                 depth_computing_param={'window': '100D', 'on': 'report_date'},
                 breadth_computing_method='quantile',
                 breadth_computing_param={'score_levels': [0.1, 0.3, 0.5, 0.7, 0.9]}) -> None:
        super().__init__(FinanceFactor, entity_ids, entity_type, exchanges, codes, the_timestamp, start_timestamp,
                         end_timestamp, columns, filters, order, limit, provider, level,
                         category_field, time_field, trip_timestamp, auto_load, keep_all_timestamp, fill_method,
                         effective_number, depth_computing_method, depth_computing_param, breadth_computing_method,
                         breadth_computing_param)


if __name__ == '__main__':
    factor = FinanceGrowthFactor(start_timestamp='2018-01-01',
                                 end_timestamp='2018-12-31',
                                 codes=['000338', '000778', '601318'],
                                 auto_load=True)
    factor.draw_result(chart='bar')
