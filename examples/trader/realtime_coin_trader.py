# -*- coding: utf-8 -*-
from zvt.domain.common import TradingLevel

from zvt.factors.technical_factor import CrossMaFactor
from zvt.selectors.selector import TargetSelector
from zvt.trader.impls import StockTrader


class MyStockTrader(StockTrader):
    def init_selectors(self, security_list, security_type, exchanges, codes, start_timestamp, end_timestamp):
        myselector = TargetSelector(security_list=security_list, security_type=security_type, exchanges=exchanges,
                                    codes=codes, start_timestamp=start_timestamp, end_timestamp=end_timestamp)

        myselector.add_filter_factor(
            CrossMaFactor(security_list=security_list, security_type=security_type, exchanges=exchanges,
                          codes=codes, start_timestamp=start_timestamp, end_timestamp=end_timestamp))

        self.selectors.append(myselector)


if __name__ == '__main__':
    MyStockTrader(codes=['000338'], level=TradingLevel.LEVEL_1DAY, start_timestamp='2018-01-01',
                  end_timestamp='2019-06-30').run()
