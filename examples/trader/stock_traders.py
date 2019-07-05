# -*- coding: utf-8 -*-
from zvt.domain.common import TradingLevel

from zvt.factors.technical_factor import CrossMaFactor, BullFactor
from zvt.selectors.selector import TargetSelector
from zvt.settings import SAMPLE_STOCK_CODES
from zvt.trader.impls import StockTrader


# make sure run init_data_sample.py to init the data sample at first
# or you could change settings.DATA_PATH to your data path,and run the recorders for the data
class MyMaTrader(StockTrader):
    def init_selectors(self, security_list, security_type, exchanges, codes, start_timestamp, end_timestamp):
        myselector = TargetSelector(security_list=security_list, security_type=security_type, exchanges=exchanges,
                                    codes=codes, start_timestamp=start_timestamp, end_timestamp=end_timestamp,
                                    provider='joinquant')

        myselector.add_filter_factor(
            CrossMaFactor(security_list=security_list, security_type=security_type, exchanges=exchanges,
                          codes=codes, start_timestamp=start_timestamp, end_timestamp=end_timestamp))

        self.selectors.append(myselector)


class MyBullTrader(StockTrader):
    def init_selectors(self, security_list, security_type, exchanges, codes, start_timestamp, end_timestamp):
        myselector = TargetSelector(security_list=security_list, security_type=security_type, exchanges=exchanges,
                                    codes=codes, start_timestamp=start_timestamp, end_timestamp=end_timestamp,
                                    provider='joinquant')

        myselector.add_filter_factor(
            BullFactor(security_list=security_list, security_type=security_type, exchanges=exchanges,
                       codes=codes, start_timestamp=start_timestamp, end_timestamp=end_timestamp))

        self.selectors.append(myselector)


if __name__ == '__main__':
    # single stock with cross ma factor
    MyMaTrader(codes=['000338'], level=TradingLevel.LEVEL_1DAY, start_timestamp='2018-01-01',
               end_timestamp='2019-06-30', trader_name='000338_ma_trader').run()

    # single stock with bull factor
    MyBullTrader(codes=['000338'], level=TradingLevel.LEVEL_1DAY, start_timestamp='2018-01-01',
                 end_timestamp='2019-06-30', trader_name='000338_bull_trader').run()

    #  multiple stocks with cross ma factor
    MyMaTrader(codes=SAMPLE_STOCK_CODES, level=TradingLevel.LEVEL_1DAY, start_timestamp='2018-01-01',
               end_timestamp='2019-06-30', trader_name='sample_stocks_ma_trader').run()

    # multiple stocks with bull factor
    MyBullTrader(codes=SAMPLE_STOCK_CODES, level=TradingLevel.LEVEL_1DAY, start_timestamp='2018-01-01',
                 end_timestamp='2019-06-30', trader_name='sample_stocks_bull_trader').run()
