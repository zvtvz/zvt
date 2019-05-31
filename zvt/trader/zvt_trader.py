# -*- coding: utf-8 -*-
from zvt.domain import Provider
from zvt.selectors.zvt_selector import TechnicalSelector, FundamentalSelector
from zvt.trader.trader import Trader


class FoolTrader(Trader):
    def init_selectors(self, security_type, exchanges, codes, start_timestamp, end_timestamp):
        self.selectors = []

        ma_selector = TechnicalSelector(security_type=security_type, exchanges=exchanges, codes=codes,
                                        start_timestamp=start_timestamp,
                                        end_timestamp=end_timestamp)
        ma_selector.run()

        finance_selector = FundamentalSelector(security_type=security_type, exchanges=exchanges, codes=codes,
                                               start_timestamp=start_timestamp, end_timestamp=end_timestamp)
        finance_selector.run()

        self.selectors.append(ma_selector)
        self.selectors.append(finance_selector)

        print(ma_selector.get_df())
        print(finance_selector.get_df())


if __name__ == '__main__':
    FoolTrader(start_timestamp='2019-01-01',
               end_timestamp='2019-05-01', provider=Provider.NETEASE).run()
