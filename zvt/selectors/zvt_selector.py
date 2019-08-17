# -*- coding: utf-8 -*-
import time

from zvdata.structs import IntervalLevel
from zvt.factors.finance_factor import FinanceGrowthFactor
from zvt.factors.technical_factor import CrossMaFactor
from zvt.selectors.selector import TargetSelector


class TechnicalSelector(TargetSelector):
    def __init__(self, entity_ids=None, entity_type='stock', exchanges=['sh', 'sz'], codes=None,
                 the_timestamp=None, start_timestamp=None, end_timestamp=None, threshold=0.8,
                 level=IntervalLevel.LEVEL_1DAY,
                 provider='netease') -> None:
        super().__init__(entity_ids, entity_type, exchanges, codes, the_timestamp, start_timestamp, end_timestamp,
                         threshold, level, provider)

    def init_factors(self, entity_ids, entity_type, exchanges, codes, the_timestamp, start_timestamp,
                     end_timestamp):
        ma_factor = CrossMaFactor(entity_ids=entity_ids, entity_type=entity_type, exchanges=exchanges,
                                  codes=codes, the_timestamp=the_timestamp, start_timestamp=start_timestamp,
                                  end_timestamp=end_timestamp, provider=self.provider, level=self.level)

        self.must_factors = [ma_factor]


class FundamentalSelector(TargetSelector):
    def init_factors(self, entity_ids, entity_type, exchanges, codes, the_timestamp, start_timestamp,
                     end_timestamp):
        factor = FinanceGrowthFactor(entity_ids=entity_ids, entity_type=entity_type, exchanges=exchanges,
                                     codes=codes, the_timestamp=the_timestamp, start_timestamp=start_timestamp,
                                     end_timestamp=end_timestamp, keep_all_timestamp=True, provider=self.provider)
        self.score_factors = [factor]


if __name__ == '__main__':
    ma_selector = TechnicalSelector(entity_ids=['coin_binance_EOS/USDT'], provider='ccxt',
                                    entity_type='coin', start_timestamp='2019-01-01',
                                    end_timestamp='2019-06-05', level=IntervalLevel.LEVEL_5MIN)
    ma_selector.run()
    print(ma_selector.get_result_df())

    while True:
        ma_selector.move_on()
        print(ma_selector.get_result_df())
        time.sleep(10)
