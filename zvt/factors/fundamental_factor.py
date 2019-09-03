# -*- coding: utf-8 -*-
from typing import List, Union

import pandas as pd

from zvdata.factor import Factor
from zvdata.structs import IntervalLevel
from zvt.domain import FinanceFactor, BalanceSheet


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


if __name__ == '__main__':
    f1 = FinanceBaseFactor(filters=[FinanceFactor.roe >= 0.15], start_timestamp='2018-12-31', time_field='report_date')
    f2 = FinanceBaseFactor(data_schema=BalanceSheet, filters=[BalanceSheet.accounts_receivable <= BalanceSheet.equity],
                           start_timestamp='2018-12-31', time_field='report_date')
    print(f1.data_df)
    print(f2.data_df)

    df = f1.data_df.join(f2.data_df)

    print(df)
