# -*- coding: utf-8 -*-
from typing import List

from zvt.selectors.zvt_selector import FundamentalSelector
from zvt.settings import SAMPLE_STOCK_CODES
from zvt.trader.examples.coin_trader import *


class CoinTrader(Trader):
    security_type = SecurityType.coin

    def __init__(self,
                 security_list: List[str] = None,
                 exchanges: List[str] = ['binance'],
                 codes: List[str] = ['EOS/USDT'],
                 start_timestamp: Union[str, pd.Timestamp] = '2019-06-15',
                 end_timestamp: Union[str, pd.Timestamp] = '2019-06-30',
                 provider: Union[str, Provider] = 'ccxt',
                 level: Union[str, TradingLevel] = TradingLevel.LEVEL_5MIN,
                 trader_name: str = None,
                 real_time: bool = False,
                 kdata_use_begin_time: bool = True) -> None:
        super().__init__(security_list, SecurityType.coin, exchanges, codes, start_timestamp, end_timestamp, provider,
                         level, trader_name, real_time, kdata_use_begin_time=kdata_use_begin_time)

    def init_selectors(self, security_list, security_type, exchanges, codes, start_timestamp, end_timestamp):
        self.selectors = []

        selector1 = TechnicalSelector(security_list=security_list, security_type=security_type,
                                      exchanges=exchanges, codes=codes,
                                      start_timestamp=start_timestamp,
                                      end_timestamp=end_timestamp, level=TradingLevel.LEVEL_1MIN,
                                      provider='ccxt')
        selector1.run()

        # selector2 = TechnicalSelector(security_list=security_list, security_type=security_type,
        #                                    exchanges=exchanges, codes=codes,
        #                                    start_timestamp=start_timestamp,
        #                                    end_timestamp=end_timestamp, level=TradingLevel.LEVEL_5MIN,
        #                                    provider='ccxt')
        # selector2.run()

        self.selectors.append(selector1)
        # self.selectors.append(selector2)

    @classmethod
    def get_constructor_meta(cls):
        meta = super().get_constructor_meta()
        meta.metas['security_type'] = marshal_object_for_ui(cls.security_type)
        return meta


class StockTrader(Trader):
    security_type = SecurityType.stock

    def __init__(self, security_list: List[str] = None,
                 exchanges: List[str] = ['sh', 'sz'],
                 codes: List[str] = None,
                 start_timestamp: Union[str, pd.Timestamp] = None,
                 end_timestamp: Union[str, pd.Timestamp] = None,
                 provider: Union[str, Provider] = 'joinquant',
                 level: Union[str, TradingLevel] = TradingLevel.LEVEL_1DAY,
                 trader_name: str = None,
                 real_time: bool = False,
                 kdata_use_begin_time: bool = False) -> None:
        super().__init__(security_list, SecurityType.stock, exchanges, codes, start_timestamp, end_timestamp, provider,
                         level, trader_name, real_time, kdata_use_begin_time)

    def init_selectors(self, security_list, security_type, exchanges, codes, start_timestamp, end_timestamp):
        self.selectors = []

        technical_selector = TechnicalSelector(security_list=security_list, security_type=security_type,
                                               exchanges=exchanges,
                                               codes=codes,
                                               start_timestamp=start_timestamp,
                                               end_timestamp=end_timestamp)
        technical_selector.run()

        fundamental_selector = FundamentalSelector(security_list=security_list, security_type=security_type,
                                                   exchanges=exchanges, codes=codes,
                                                   start_timestamp=start_timestamp, end_timestamp=end_timestamp)
        fundamental_selector.run()

        self.selectors.append(technical_selector)
        self.selectors.append(fundamental_selector)

    @classmethod
    def get_constructor_meta(cls):
        meta = super().get_constructor_meta()
        meta.metas['security_type'] = marshal_object_for_ui(cls.security_type)
        return meta


if __name__ == '__main__':
    # CoinTrader(start_timestamp='2019-06-03',
    #            end_timestamp='2019-06-22',
    #            level=TradingLevel.LEVEL_1MIN,
    #            security_list=['coin_binance_EOS/USDT'],
    #            real_time=False,
    #            kdata_use_begin_time=True).run()

    StockTrader(start_timestamp='2015-01-01',
                end_timestamp='2019-06-21',
                provider=Provider.NETEASE,
                codes=SAMPLE_STOCK_CODES,
                level=TradingLevel.LEVEL_1DAY).run()
