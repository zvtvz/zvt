# -*- coding: utf-8 -*-
from zvt.domain import SecurityType, TradingLevel
from zvt.factors.finance_factor import FinanceGrowthFactor
from zvt.factors.technical_factor import CrossMaFactor
from zvt.selectors.selector import TargetSelector


class TechnicalSelector(TargetSelector):
    def __init__(self, security_type=SecurityType.stock, exchanges=['sh', 'sz'], codes=None, the_timestamp=None,
                 start_timestamp=None, end_timestamp=None, threshold=0.8, level=TradingLevel.LEVEL_1DAY,
                 provider='netease') -> None:
        super().__init__(security_type, exchanges, codes, the_timestamp, start_timestamp, end_timestamp, threshold,
                         level, provider)

    def init_factors(self, security_type, exchanges, codes, the_timestamp, start_timestamp, end_timestamp):
        ma_factor = CrossMaFactor(security_type=security_type, exchanges=exchanges, codes=codes,
                                  the_timestamp=the_timestamp, start_timestamp=start_timestamp,
                                  end_timestamp=end_timestamp, provider=self.provider, level=self.level)
        ma_factor.run()

        self.must_factors = [ma_factor]


class FundamentalSelector(TargetSelector):
    def init_factors(self, security_type, exchanges, codes, the_timestamp, start_timestamp, end_timestamp):
        factor = FinanceGrowthFactor(security_type=security_type, exchanges=exchanges, codes=codes,
                                     the_timestamp=the_timestamp, start_timestamp=start_timestamp,
                                     end_timestamp=end_timestamp, keep_all_timestamp=True, provider=self.provider)
        factor.run()
        self.score_factors = [factor]


if __name__ == '__main__':
    s = FundamentalSelector(start_timestamp='2018-01-01', end_timestamp='2019-05-01')
    s.run()

    print(s.get_df())

    # ma_selector = MaSelector(codes=['000338'], start_timestamp='2018-01-01', end_timestamp='2019-05-01')
    # ma_selector.run()
    # print(ma_selector.get_df())
