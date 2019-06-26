# -*- coding: utf-8 -*-
from typing import List, Union

import pandas as pd

from zvt.domain import SimAccount, TradingLevel, Order
from zvt.reader.reader import DataReader


class AccountReader(DataReader):
    def __init__(self,
                 the_timestamp: Union[str, pd.Timestamp] = None,
                 start_timestamp: Union[str, pd.Timestamp] = None,
                 end_timestamp: Union[str, pd.Timestamp] = None,
                 columns: List = None,
                 filters: List = None,
                 level: TradingLevel = TradingLevel.LEVEL_1DAY,
                 real_time: bool = False,
                 refresh_interval: int = 10,
                 trader_names: List[str] = None) -> None:
        self.trader_names = trader_names

        self.filters = filters

        if self.trader_names:
            filter = [SimAccount.trader_name == name for name in self.trader_names]
            if self.filters:
                self.filters += filter
            else:
                self.filters = filter
        super().__init__(SimAccount, None, None, None, None, the_timestamp, start_timestamp,
                         end_timestamp, columns, self.filters, 'zvt', level, real_time, refresh_interval,
                         category_field='trader_name')


class OrderReader(DataReader):
    def __init__(self,
                 the_timestamp: Union[str, pd.Timestamp] = None,
                 start_timestamp: Union[str, pd.Timestamp] = None,
                 end_timestamp: Union[str, pd.Timestamp] = None,
                 columns: List = None,
                 filters: List = None,
                 level: TradingLevel = None,
                 real_time: bool = False,
                 refresh_interval: int = 10,
                 trader_names: List[str] = None) -> None:
        self.trader_names = trader_names

        self.filters = filters

        if self.trader_names:
            filter = [Order.trader_name == name for name in self.trader_names]
            if self.filters:
                self.filters += filter
            else:
                self.filters = filter

        super().__init__(Order, None, None, None, None, the_timestamp, start_timestamp,
                         end_timestamp, columns, self.filters, 'zvt', level, real_time, refresh_interval,
                         category_field='trader_name')


if __name__ == '__main__':
    reader = OrderReader(trader_names=['cointrader'])
    reader.draw(value_fields='order_amount')
