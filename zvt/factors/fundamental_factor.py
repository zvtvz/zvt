# -*- coding: utf-8 -*-
from typing import List, Union

import pandas as pd

from zvdata.factor import Factor
from zvdata import IntervalLevel
from zvt.domain import FinanceFactor


class FinanceBaseFactor(Factor):
    def __init__(self,
                 data_schema=FinanceFactor,
                 entity_ids: List[str] = None,
                 entity_type: str = 'stock',
                 exchanges: List[str] = ['sh', 'sz'],
                 codes: List[str] = None,
                 the_timestamp: Union[str, pd.Timestamp] = None,
                 start_timestamp: Union[str, pd.Timestamp] = None,
                 end_timestamp: Union[str, pd.Timestamp] = None,
                 columns: List = None,
                 filters: List = None,
                 order: object = None,
                 limit: int = None,
                 provider: str = 'eastmoney',
                 level: Union[str, IntervalLevel] = IntervalLevel.LEVEL_1DAY,
                 category_field: str = 'entity_id',
                 time_field: str = 'timestamp',
                 trip_timestamp: bool = True,
                 auto_load: bool = True,
                 keep_all_timestamp: bool = False,
                 fill_method: str = 'ffill',
                 effective_number: int = 10) -> None:
        if not columns:
            columns = data_schema.important_cols()

        super().__init__(data_schema, entity_ids, entity_type, exchanges, codes, the_timestamp, start_timestamp,
                         end_timestamp, columns, filters, order, limit, provider, level, category_field, time_field,
                         trip_timestamp, auto_load, keep_all_timestamp, fill_method, effective_number)


class GoodCompanyFactor(FinanceBaseFactor):
    def __init__(self,
                 entity_ids: List[str] = None,
                 codes: List[str] = None,
                 the_timestamp: Union[str, pd.Timestamp] = None,
                 start_timestamp: Union[str, pd.Timestamp] = None,
                 end_timestamp: Union[str, pd.Timestamp] = None,
                 columns: List = [FinanceFactor.roe,
                                  FinanceFactor.op_income_growth_yoy,
                                  FinanceFactor.net_profit_growth_yoy],
                 filters: List = [FinanceFactor.roe > 0.03,
                                  FinanceFactor.op_income_growth_yoy >= 0.1,
                                  FinanceFactor.net_profit_growth_yoy >= 0.1],
                 order: object = None,
                 limit: int = None,
                 provider: str = 'eastmoney',
                 level: Union[str, IntervalLevel] = IntervalLevel.LEVEL_1DAY,
                 category_field: str = 'entity_id',
                 time_field: str = 'timestamp',
                 trip_timestamp: bool = True,
                 auto_load: bool = True,
                 keep_all_timestamp: bool = False,
                 fill_method: str = 'ffill',
                 effective_number: int = 10,
                 # 3 years
                 window='1095d') -> None:
        self.window = window
        super().__init__(FinanceFactor, entity_ids, 'stock', ['sh', 'sz'], codes, the_timestamp, start_timestamp,
                         end_timestamp, columns, filters, order, limit, provider, level, category_field, time_field,
                         trip_timestamp, auto_load, keep_all_timestamp, fill_method, effective_number)

    def do_compute(self):
        self.depth_df = pd.DataFrame(index=self.data_df.index, columns=['count'], data=1)

        self.depth_df = self.depth_df.reset_index(level=1)

        self.depth_df = self.depth_df.groupby(level=0).rolling(window=self.window, on=self.time_field).count()

        self.depth_df = self.depth_df.reset_index(level=0, drop=True)
        self.depth_df = self.depth_df.set_index(self.time_field, append=True)

        self.depth_df = self.depth_df.loc[(slice(None), slice(self.start_timestamp, self.end_timestamp)), :]

        self.logger.info('factor:{},depth_df:\n{}'.format(self.factor_name, self.depth_df))

        self.result_df = self.depth_df.apply(lambda x: x >= 12)

        self.logger.info('factor:{},result_df:\n{}'.format(self.factor_name, self.result_df))


if __name__ == '__main__':
    f1 = GoodCompanyFactor(start_timestamp='2000-01-01')
    print(f1.data_df)
