# -*- coding: utf-8 -*-
from typing import Union

import pandas as pd

from zvt.domain import TradingLevel, Provider, SecurityType
from zvt.factors.technical_factor import CrossMaFactor
from zvt.selectors.selector import TargetSelector
from zvt.trader.trader import Trader
from zvt.utils.utils import marshal_object_for_ui


class CoinTrader(Trader):
    security_type = SecurityType.coin


class SingleCoinTrader(CoinTrader):
    def __init__(self,
                 security: str = 'coin_binance_EOS/USDT',
                 start_timestamp: Union[str, pd.Timestamp] = '2018-06-01',
                 end_timestamp: Union[str, pd.Timestamp] = '2019-06-30',
                 provider: Union[str, Provider] = 'ccxt',
                 level: Union[str, TradingLevel] = TradingLevel.LEVEL_1DAY,
                 trader_name: str = None,
                 real_time: bool = False,
                 kdata_use_begin_time: bool = True) -> None:
        super().__init__([security], SecurityType.coin, None, None, start_timestamp, end_timestamp, provider,
                         level, trader_name, real_time, kdata_use_begin_time=kdata_use_begin_time)

    def init_selectors(self, security_list, security_type, exchanges, codes, start_timestamp, end_timestamp):
        my_selector = TargetSelector(security_list=security_list, security_type=security_type, exchanges=exchanges,
                                     codes=codes, start_timestamp=start_timestamp,
                                     end_timestamp=end_timestamp)
        # add the factors
        my_selector \
            .add_filter_factor(CrossMaFactor(security_list=security_list,
                                             security_type=security_type,
                                             exchanges=exchanges,
                                             codes=codes,
                                             start_timestamp=start_timestamp,
                                             end_timestamp=end_timestamp,
                                             level=TradingLevel.LEVEL_1MIN,
                                             provider='ccxt'))
        self.selectors.append(my_selector)

    @classmethod
    def get_constructor_meta(cls):
        meta = super().get_constructor_meta()
        meta.metas['security_type'] = marshal_object_for_ui(cls.security_type)
        return meta


if __name__ == '__main__':
    SingleCoinTrader(level=TradingLevel.LEVEL_1MIN, start_timestamp='2019-06-29', end_timestamp='2019-07-01',
                     real_time=True).run()
