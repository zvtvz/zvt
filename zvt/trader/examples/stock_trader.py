# -*- coding: utf-8 -*-
from typing import Union

import pandas as pd

from zvt.domain import TradingLevel, Provider, SecurityType
from zvt.selectors.zvt_selector import TechnicalSelector
from zvt.trader.trader import Trader
from zvt.utils.utils import marshal_object_for_ui


class SingleStockTrader(Trader):
    security_type = SecurityType.stock

    def __init__(self,
                 security: str = 'stock_sz_000338',
                 start_timestamp: Union[str, pd.Timestamp] = '2005-01-01',
                 end_timestamp: Union[str, pd.Timestamp] = '2019-06-30',
                 provider: Union[str, Provider] = 'joinquant',
                 level: Union[str, TradingLevel] = TradingLevel.LEVEL_1DAY,
                 trader_name: str = None,
                 real_time: bool = False,
                 kdata_use_begin_time: bool = True) -> None:
        super().__init__([security], SecurityType.stock, None, None, start_timestamp, end_timestamp, provider,
                         level, trader_name, real_time, kdata_use_begin_time=kdata_use_begin_time)

    def init_selectors(self, security_list, security_type, exchanges, codes, start_timestamp, end_timestamp):
        self.selectors = []

        selector1 = TechnicalSelector(security_list=security_list, security_type=security_type,
                                      exchanges=exchanges, codes=codes,
                                      start_timestamp=start_timestamp,
                                      end_timestamp=end_timestamp, level=TradingLevel.LEVEL_1DAY,
                                      provider='joinquant')
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


if __name__ == '__main__':
    SingleStockTrader(security='stock_sz_000338', start_timestamp='2018-01-01').run()
