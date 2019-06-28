# -*- coding: utf-8 -*-
from typing import Union, List

import pandas as pd

from zvt.domain import TradingLevel, Provider, SecurityType
from zvt.factors.finance_factor import FinanceGrowthFactor
from zvt.factors.technical_factor import BullFactor, CrossMaFactor
from zvt.selectors.selector import TargetSelector
from zvt.settings import SAMPLE_STOCK_CODES
from zvt.trader.trader import Trader
from zvt.utils.utils import marshal_object_for_ui


class StockTrader(Trader):
    security_type = SecurityType.stock


class MultipleStockTrader(StockTrader):
    def __init__(self,
                 security_list: List[str] = None,
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
        my_selector = TargetSelector(security_list=security_list, security_type=security_type, exchanges=exchanges,
                                     codes=codes, start_timestamp=start_timestamp,
                                     end_timestamp=end_timestamp)
        # add the factors
        my_selector \
            .add_filter_factor(BullFactor(security_list=security_list,
                                          security_type=security_type,
                                          exchanges=exchanges,
                                          codes=codes,
                                          start_timestamp=start_timestamp,
                                          end_timestamp=end_timestamp,
                                          level=TradingLevel.LEVEL_1DAY))
            # .add_score_factor(FinanceGrowthFactor(security_list=security_list,
            #                                       security_type=security_type,
            #                                       exchanges=exchanges,
            #                                       codes=codes,
            #                                       start_timestamp=start_timestamp,
            #                                       end_timestamp=end_timestamp,
            #                                       level=TradingLevel.LEVEL_1DAY))
        self.selectors.append(my_selector)


class SingleStockTrader(StockTrader):
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
                                             level=TradingLevel.LEVEL_1DAY))
        self.selectors.append(my_selector)

    @classmethod
    def get_constructor_meta(cls):
        meta = super().get_constructor_meta()
        meta.metas['security_type'] = marshal_object_for_ui(cls.security_type)
        return meta


if __name__ == '__main__':
    # SingleStockTrader(security='stock_sz_000338', start_timestamp='2018-01-01').run()

    # just get hs300 securities
    # security_list = get_securities_in_blocks(block_names=['HS300_'])
    # MultipleStockTrader(security_list=security_list, start_timestamp='2018-01-01', end_timestamp='2019-06-25').run()
    MultipleStockTrader(codes=SAMPLE_STOCK_CODES, start_timestamp='2018-01-01', end_timestamp='2019-06-25').run()
