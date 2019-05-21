# -*- coding: utf-8 -*-
from zvt.factors.finance_factor import FinanceGrowthFactor
from zvt.factors.technical_factor import CrossMaFactor
from zvt.selectors.selector import TargetSelector


class MaSelector(TargetSelector):
    def init_factors(self, security_type, exchanges, codes, the_timestamp, start_timestamp, end_timestamp):
        factor = CrossMaFactor(security_type=security_type, exchanges=exchanges, codes=codes,
                               the_timestamp=the_timestamp, start_timestamp=start_timestamp,
                               end_timestamp=end_timestamp)
        factor.run()

        self.must_factors = [factor]


class FinanceSelector(TargetSelector):
    def init_factors(self, security_type, exchanges, codes, the_timestamp, start_timestamp, end_timestamp):
        factor = FinanceGrowthFactor(security_type=security_type, exchanges=exchanges, codes=codes,
                                     the_timestamp=the_timestamp, start_timestamp=start_timestamp,
                                     end_timestamp=end_timestamp, keep_all_timestamp=True)
        factor.run()
        self.score_factors = [factor]


if __name__ == '__main__':
    s = FinanceSelector(start_timestamp='2018-01-01', end_timestamp='2019-05-01')
    s.run()

    print(s.df)
