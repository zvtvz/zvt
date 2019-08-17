# -*- coding: utf-8 -*-
from typing import List, Union

import pandas as pd

from zvdata.structs import IntervalLevel
from zvt.trader.trader import Trader


class CoinTrader(Trader):
    entity_type = 'coin'

    def __init__(self,
                 entity_ids: List[str] = None,
                 exchanges: List[str] = ['huobipro'],
                 codes: List[str] = None,
                 start_timestamp: Union[str, pd.Timestamp] = None,
                 end_timestamp: Union[str, pd.Timestamp] = None,
                 provider: str = 'ccxt',
                 level: Union[str, IntervalLevel] = IntervalLevel.LEVEL_1DAY,
                 trader_name: str = None,
                 real_time: bool = False,
                 kdata_use_begin_time: bool = True) -> None:
        super().__init__(entity_ids, exchanges, codes, start_timestamp, end_timestamp, provider, level, trader_name,
                         real_time, kdata_use_begin_time)


class StockTrader(Trader):
    entity_type = 'stock'

    def __init__(self, entity_ids: List[str] = None,
                 exchanges: List[str] = ['sh', 'sz'],
                 codes: List[str] = None,
                 start_timestamp: Union[str, pd.Timestamp] = None,
                 end_timestamp: Union[str, pd.Timestamp] = None,
                 provider: str = 'joinquant',
                 level: Union[str, IntervalLevel] = IntervalLevel.LEVEL_1DAY,
                 trader_name: str = None,
                 real_time: bool = False,
                 kdata_use_begin_time: bool = False) -> None:
        super().__init__(entity_ids, exchanges, codes, start_timestamp, end_timestamp, provider, level, trader_name,
                         real_time, kdata_use_begin_time)
