# -*- coding: utf-8 -*-
import pandas as pd

from zvt.factors.examples.technical_factor import CrossMaFactor
from zvt.selector.selector import TargetSelector


class MaSelector(TargetSelector):
    def init_factors(self, security_type, exchanges, codes, the_timestamp, start_timestamp, end_timestamp):
        factor = CrossMaFactor(security_type=security_type, exchanges=exchanges, codes=codes,
                               the_timestamp=the_timestamp, window=pd.DateOffset(days=30),
                               start_timestamp=start_timestamp,
                               end_timestamp=end_timestamp)
        factor.run()

        self.must_factors = [factor]


if __name__ == '__main__':
    s = MaSelector(start_timestamp='2017-01-01', end_timestamp='2019-05-01')
    s.run()
