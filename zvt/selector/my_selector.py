# -*- coding: utf-8 -*-
import pandas as pd

from zvt.factors.finance_factor import FinanceGrowthFactor
from zvt.selector.selector import TargetSelector


class MySelector(TargetSelector):
    def init_factors(self, security_type, exchanges, the_timestamp, start_timestamp, end_timestamp):
        factor = FinanceGrowthFactor(window=pd.DateOffset(days=365), start_timestamp=start_timestamp,
                                     end_timestamp=end_timestamp)
        factor.run()

        self.score_factors = [factor.df]


if __name__ == '__main__':
    s = MySelector(start_timestamp='2017-12-31', end_timestamp='2018-12-31')
    s.run()
