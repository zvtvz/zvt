# -*- coding: utf-8 -*-
from zvt.factors.finance_factor import FinanceGrowthFactor
from zvt.selectors.selector import TargetSelector


class FundamentalSelector(TargetSelector):
    def init_factors(self, security_list, security_type, exchanges, codes, the_timestamp, start_timestamp,
                     end_timestamp):
        factor = FinanceGrowthFactor(security_list=security_list, security_type=security_type, exchanges=exchanges,
                                     codes=codes, the_timestamp=the_timestamp, start_timestamp=start_timestamp,
                                     end_timestamp=end_timestamp, keep_all_timestamp=True, provider='eastmoney')
        self.score_factors.append(factor)


if __name__ == '__main__':
    selector: TargetSelector = FundamentalSelector(start_timestamp='2018-01-01', end_timestamp='2019-06-30')
    selector.run()
    selector.draw()
