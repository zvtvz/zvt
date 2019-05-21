# -*- coding: utf-8 -*-
from zvt.selectors.zvt_selector import MaSelector, FinanceSelector
from zvt.trader.trader import Trader


class FoolTrader(Trader):
    def init_selectors(self, security_type, exchanges, codes, start_timestamp, end_timestamp):
        self.selectors = []

        ma_selector = MaSelector(security_type=security_type, exchanges=exchanges, codes=codes,
                                 start_timestamp=start_timestamp,
                                 end_timestamp=end_timestamp)
        ma_selector.run()

        finance_selector = FinanceSelector(security_type=security_type, exchanges=exchanges, codes=codes,
                                           start_timestamp=start_timestamp, end_timestamp=end_timestamp)
        finance_selector.run()

        self.selectors.append(ma_selector)
        self.selectors.append(finance_selector)

        print(ma_selector.get_df())
        print(finance_selector.get_df())


if __name__ == '__main__':
    FoolTrader(start_timestamp='2014-01-01',
               end_timestamp='2019-05-01').run()
