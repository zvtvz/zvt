# -*- coding: utf-8 -*-
from zvdata import IntervalLevel
from zvt.factors.ma.ma_factor import CrossMaFactor
from zvt.factors.target_selector import TargetSelector
from zvt.factors.technical_factor import BullFactor

from zvt.trader.trader import StockTrader


class MyMaTrader(StockTrader):
    def init_selectors(self, entity_ids, entity_type, exchanges, codes, start_timestamp, end_timestamp):
        myselector = TargetSelector(entity_ids=entity_ids, entity_type=entity_type, exchanges=exchanges,
                                    codes=codes, start_timestamp=start_timestamp, end_timestamp=end_timestamp,
                                    provider='joinquant')

        myselector.add_filter_factor(
            CrossMaFactor(entity_ids=entity_ids, entity_type=entity_type, exchanges=exchanges,
                          codes=codes, start_timestamp=start_timestamp, end_timestamp=end_timestamp,
                          windows=[5, 10], persist_factor=False))

        self.selectors.append(myselector)


class MyBullTrader(StockTrader):
    def init_selectors(self, entity_ids, entity_type, exchanges, codes, start_timestamp, end_timestamp):
        myselector = TargetSelector(entity_ids=entity_ids, entity_type=entity_type, exchanges=exchanges,
                                    codes=codes, start_timestamp=start_timestamp, end_timestamp=end_timestamp,
                                    provider='joinquant')

        myselector.add_filter_factor(
            BullFactor(entity_ids=entity_ids, entity_type=entity_type, exchanges=exchanges,
                       codes=codes, start_timestamp=start_timestamp, end_timestamp=end_timestamp))

        self.selectors.append(myselector)


if __name__ == '__main__':
    # single stock with cross ma factor
    MyMaTrader(codes=['000338'], level=IntervalLevel.LEVEL_1DAY, start_timestamp='2018-01-01',
               end_timestamp='2019-06-30', trader_name='000338_ma_trader').run()

    # single stock with bull factor
    # MyBullTrader(codes=['000338'], level=IntervalLevel.LEVEL_1DAY, start_timestamp='2018-01-01',
    #              end_timestamp='2019-06-30', trader_name='000338_bull_trader').run()

    #  multiple stocks with cross ma factor
    # MyMaTrader(codes=SAMPLE_STOCK_CODES, level=IntervalLevel.LEVEL_1DAY, start_timestamp='2018-01-01',
    #            end_timestamp='2019-06-30', trader_name='sample_stocks_ma_trader').run()

    # multiple stocks with bull factor
    # MyBullTrader(codes=SAMPLE_STOCK_CODES, level=IntervalLevel.LEVEL_1DAY, start_timestamp='2018-01-01',
    #              end_timestamp='2019-06-30', trader_name='sample_stocks_bull_trader').run()
