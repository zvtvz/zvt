# -*- coding: utf-8 -*-
from zvt.domain import TradingLevel, Provider
from zvt.selectors.zvt_selector import TechnicalSelector, FundamentalSelector
from zvt.trader.trader import Trader


class MultipleLevelTrader(Trader):
    def init_selectors(self, security_type, exchanges, codes, start_timestamp, end_timestamp):
        self.selectors = []

        ma_1d_selector = TechnicalSelector(security_type=security_type, exchanges=exchanges, codes=codes,
                                           start_timestamp=start_timestamp,
                                           end_timestamp=end_timestamp, level=TradingLevel.LEVEL_1DAY,
                                           provider='netease')
        ma_1d_selector.run()

        ma_1h_selector = TechnicalSelector(security_type=security_type, exchanges=exchanges, codes=codes,
                                           start_timestamp=start_timestamp,
                                           end_timestamp=end_timestamp, level=TradingLevel.LEVEL_1HOUR,
                                           provider='joinquant')
        ma_1h_selector.run()

        finance_selector = FundamentalSelector(security_type=security_type, exchanges=exchanges, codes=codes,
                                               start_timestamp=start_timestamp, end_timestamp=end_timestamp)
        finance_selector.run()

        self.selectors.append(ma_1d_selector)
        self.selectors.append(ma_1h_selector)
        self.selectors.append(finance_selector)

        print(ma_1d_selector.get_df())
        print(ma_1h_selector.get_df())


if __name__ == '__main__':
    MultipleLevelTrader(provider=Provider.JOINQUANT,
                        start_timestamp='2019-01-01',
                        end_timestamp='2019-05-01', trading_level=TradingLevel.LEVEL_1HOUR).run()
