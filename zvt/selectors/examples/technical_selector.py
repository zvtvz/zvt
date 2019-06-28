# -*- coding: utf-8 -*-

from zvt.domain import SecurityType, TradingLevel
from zvt.factors.finance_factor import FinanceGrowthFactor
from zvt.factors.technical_factor import BullFactor
from zvt.selectors.selector import TargetSelector


class TechnicalSelector(TargetSelector):
    def __init__(self, security_list=None, security_type=SecurityType.stock, exchanges=['sh', 'sz'], codes=None,
                 the_timestamp=None, start_timestamp=None, end_timestamp=None, threshold=0.8,
                 level=TradingLevel.LEVEL_1DAY,
                 provider='joinquant') -> None:
        super().__init__(security_list, security_type, exchanges, codes, the_timestamp, start_timestamp, end_timestamp,
                         threshold, level, provider)

    def init_factors(self, security_list, security_type, exchanges, codes, the_timestamp, start_timestamp,
                     end_timestamp):
        bull_factor = BullFactor(security_list=security_list, security_type=security_type, exchanges=exchanges,
                                 codes=codes, the_timestamp=the_timestamp, start_timestamp=start_timestamp,
                                 end_timestamp=end_timestamp, provider=self.provider, level=self.level)

        self.filter_factors = [bull_factor]


class FundamentalSelector(TargetSelector):
    def init_factors(self, security_list, security_type, exchanges, codes, the_timestamp, start_timestamp,
                     end_timestamp):
        factor = FinanceGrowthFactor(security_list=security_list, security_type=security_type, exchanges=exchanges,
                                     codes=codes, the_timestamp=the_timestamp, start_timestamp=start_timestamp,
                                     end_timestamp=end_timestamp, keep_all_timestamp=True, provider=self.provider)
        self.score_factors = [factor]
