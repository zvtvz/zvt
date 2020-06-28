# -*- coding: utf-8 -*-
from typing import List, Union

import pandas as pd

from zvt.contract import IntervalLevel
from zvt.domain import ManagerTrading
from zvt.trader.trader import StockTrader
from zvt.utils.pd_utils import pd_is_not_null


class MySoloTrader(StockTrader):

    def __init__(self, entity_ids: List[str] = None, exchanges: List[str] = None, codes: List[str] = None,
                 start_timestamp: Union[str, pd.Timestamp] = None, end_timestamp: Union[str, pd.Timestamp] = None,
                 provider: str = None, level: Union[str, IntervalLevel] = IntervalLevel.LEVEL_1DAY,
                 trader_name: str = None, real_time: bool = False, kdata_use_begin_time: bool = False,
                 draw_result: bool = True) -> None:
        super().__init__(entity_ids, exchanges, codes, start_timestamp, end_timestamp, provider, level, trader_name,
                         real_time, kdata_use_begin_time, draw_result, solo=True)

    def on_time(self, timestamp):
        # 增持5000股以上
        long_df = ManagerTrading.query_data(start_timestamp=timestamp, end_timestamp=timestamp,
                                            filters=[ManagerTrading.volume > 5000], columns=[ManagerTrading.entity_id],
                                            order=ManagerTrading.volume.desc(), limit=10)
        # 减持5000股以上
        short_df = ManagerTrading.query_data(start_timestamp=timestamp, end_timestamp=timestamp,
                                             filters=[ManagerTrading.volume < -5000],
                                             columns=[ManagerTrading.entity_id],
                                             order=ManagerTrading.volume.asc(), limit=10)
        if pd_is_not_null(long_df) or pd_is_not_null(short_df):
            try:
                self.trade_the_targets(due_timestamp=timestamp, happen_timestamp=timestamp,
                                       long_selected=set(long_df['entity_id'].to_list()),
                                       short_selected=set(short_df['entity_id'].to_list()))
            except Exception as e:
                self.logger.error(e)


if __name__ == '__main__':
    trader = MySoloTrader(start_timestamp='2015-01-01', end_timestamp='2016-01-01')
    trader.run()
