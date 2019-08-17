# -*- coding: utf-8 -*-
from typing import List

from zvdata.structs import IntervalLevel
from zvt.selectors.zvt_selector import FundamentalSelector
from zvt.settings import SAMPLE_STOCK_CODES
from zvt.trader.examples.coin_trader import *


class CoinTrader(Trader):
    entity_type = 'coin'

    def __init__(self,
                 entity_ids: List[str] = None,
                 exchanges: List[str] = ['binance'],
                 codes: List[str] = ['EOS/USDT'],
                 start_timestamp: Union[str, pd.Timestamp] = '2019-06-15',
                 end_timestamp: Union[str, pd.Timestamp] = '2019-06-30',
                 provider: str = 'ccxt',
                 level: Union[str, IntervalLevel] = IntervalLevel.LEVEL_5MIN,
                 trader_name: str = None,
                 real_time: bool = False,
                 kdata_use_begin_time: bool = True) -> None:
        super().__init__(entity_ids, 'coin', exchanges, codes, start_timestamp, end_timestamp, provider,
                         level, trader_name, real_time, kdata_use_begin_time=kdata_use_begin_time)

    def init_selectors(self, entity_ids, entity_type, exchanges, codes, start_timestamp, end_timestamp):
        self.selectors = []

        selector1 = TechnicalSelector(entity_ids=entity_ids, entity_type=entity_type,
                                      exchanges=exchanges, codes=codes,
                                      start_timestamp=start_timestamp,
                                      end_timestamp=end_timestamp, level=IntervalLevel.LEVEL_1MIN,
                                      provider='ccxt')
        selector1.run()

        # selector2 = TechnicalSelector(entity_ids=entity_ids, entity_type=entity_type,
        #                                    exchanges=exchanges, codes=codes,
        #                                    start_timestamp=start_timestamp,
        #                                    end_timestamp=end_timestamp, level=IntervalLevel.LEVEL_5MIN,
        #                                    provider='ccxt')
        # selector2.run()

        self.selectors.append(selector1)
        # self.selectors.append(selector2)


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
        super().__init__(entity_ids, 'stock', exchanges, codes, start_timestamp, end_timestamp, provider,
                         level, trader_name, real_time, kdata_use_begin_time)

    def init_selectors(self, entity_ids, entity_type, exchanges, codes, start_timestamp, end_timestamp):
        self.selectors = []

        technical_selector = TechnicalSelector(entity_ids=entity_ids, entity_type=entity_type,
                                               exchanges=exchanges,
                                               codes=codes,
                                               start_timestamp=start_timestamp,
                                               end_timestamp=end_timestamp)
        technical_selector.run()

        fundamental_selector = FundamentalSelector(entity_ids=entity_ids, entity_type=entity_type,
                                                   exchanges=exchanges, codes=codes,
                                                   start_timestamp=start_timestamp, end_timestamp=end_timestamp)
        fundamental_selector.run()

        self.selectors.append(technical_selector)
        self.selectors.append(fundamental_selector)


if __name__ == '__main__':
    # CoinTrader(start_timestamp='2019-06-03',
    #            end_timestamp='2019-06-22',
    #            level=IntervalLevel.LEVEL_1MIN,
    #            entity_ids=['coin_binance_EOS/USDT'],
    #            real_time=False,
    #            kdata_use_begin_time=True).run()

    StockTrader(start_timestamp='2015-01-01',
                end_timestamp='2019-06-21',
                provider='netease',
                codes=SAMPLE_STOCK_CODES,
                level=IntervalLevel.LEVEL_1DAY).run()
