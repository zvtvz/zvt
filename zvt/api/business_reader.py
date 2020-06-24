# -*- coding: utf-8 -*-
from typing import List, Union

import pandas as pd

from zvt.contract import IntervalLevel
from zvt.contract.normal_data import NormalData
from zvt.contract.reader import DataReader
from zvt.domain import AccountStats, Order
from zvt.drawer.drawer import Drawer


class AccountStatsReader(DataReader):

    def __init__(self,
                 the_timestamp: Union[str, pd.Timestamp] = None,
                 start_timestamp: Union[str, pd.Timestamp] = None,
                 end_timestamp: Union[str, pd.Timestamp] = None,
                 columns: List = None,
                 filters: List = None,
                 order: object = None,
                 level: IntervalLevel = IntervalLevel.LEVEL_1DAY,
                 trader_names: List[str] = None) -> None:
        self.trader_names = trader_names

        self.filters = filters

        if self.trader_names:
            filter = [AccountStats.trader_name == name for name in self.trader_names]
            if self.filters:
                self.filters += filter
            else:
                self.filters = filter
        super().__init__(AccountStats, None, None, None, None, None, None,
                         the_timestamp, start_timestamp, end_timestamp, columns, self.filters, order, None, level,
                         category_field='trader_name', time_field='timestamp', computing_window=None)

    def draw_line(self, show=True):
        drawer = Drawer(main_data=NormalData(self.data_df.copy()[['trader_name', 'timestamp', 'all_value']],
                                             category_field='trader_name'))
        return drawer.draw_line(show=show)


class OrderReader(DataReader):
    def __init__(self,
                 the_timestamp: Union[str, pd.Timestamp] = None,
                 start_timestamp: Union[str, pd.Timestamp] = None,
                 end_timestamp: Union[str, pd.Timestamp] = None,
                 columns: List = None,
                 filters: List = None,
                 order: object = None,
                 level: IntervalLevel = None,
                 trader_names: List[str] = None) -> None:
        self.trader_names = trader_names

        self.filters = filters

        if self.trader_names:
            filter = [Order.trader_name == name for name in self.trader_names]
            if self.filters:
                self.filters += filter
            else:
                self.filters = filter

        super().__init__(Order, None, None, None, None, None, None,
                         the_timestamp, start_timestamp, end_timestamp, columns, self.filters, order, None, level,
                         category_field='trader_name', time_field='timestamp', computing_window=None)


if __name__ == '__main__':
    reader = AccountStatsReader(trader_names=['000338_ma_trader'])
    drawer = Drawer(main_data=NormalData(reader.data_df.copy()[['trader_name', 'timestamp', 'all_value']],
                                         category_field='trader_name'))
    drawer.draw_line()
