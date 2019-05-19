# -*- coding: utf-8 -*-
from zvt.factors.behavior_factor import ManagerGiveUpFactor
from zvt.selectors.zvt_selector import MaSelector
from zvt.trader.trader import Trader


class FoolTrader(Trader):
    def init_selectors(self, security_type, exchanges, codes, start_timestamp, end_timestamp):
        self.selectors = []

        ma_selector = MaSelector(security_type=security_type, exchanges=exchanges, codes=codes,
                                 start_timestamp=start_timestamp,
                                 end_timestamp=end_timestamp)
        ma_selector.run()

        # manager_behavior = ManagerGiveUpFactor(security_type=security_type, exchanges=exchanges, codes=codes,
        #                                        start_timestamp=start_timestamp, end_timestamp=end_timestamp)
        # manager_behavior.run()

        self.selectors.append(ma_selector)
        # self.selectors.append(manager_behavior)


if __name__ == '__main__':
    FoolTrader(start_timestamp='2018-10-01',
               end_timestamp='2019-04-01').run()
