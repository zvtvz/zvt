# -*- coding: utf-8 -*-
from zvt.selector.examples.zvt_selector import MaSelector
from zvt.trader.trader import Trader


class FoolTrader(Trader):
    def init_selectors(self, security_type, exchanges, codes, start_timestamp, end_timestamp):
        self.selectors = []

        basic_selector = MaSelector(security_type=security_type, exchanges=exchanges, codes=codes,
                                    start_timestamp=start_timestamp,
                                    end_timestamp=end_timestamp)
        basic_selector.run()

        self.selectors.append(basic_selector)


if __name__ == '__main__':
    FoolTrader(codes=['000020', '000021', '000023', '000025'], start_timestamp='2017-01-01',
               end_timestamp='2019-05-05').run()
