# -*- coding: utf-8 -*-
from zvdata.structs import IntervalLevel
from zvt.factors.technical_factor import BullFactor
from zvt.selectors.selector import TargetSelector
from zvt.settings import SAMPLE_STOCK_CODES


class TechnicalSelector(TargetSelector):
    def __init__(self, entity_ids=None, entity_type='stock', exchanges=['sh', 'sz'], codes=None,
                 the_timestamp=None, start_timestamp=None, end_timestamp=None, long_threshold=0.8, short_threshold=-0.8,
                 level=IntervalLevel.LEVEL_1DAY,
                 provider='joinquant') -> None:
        super().__init__(entity_ids, entity_type, exchanges, codes, the_timestamp, start_timestamp, end_timestamp,
                         long_threshold, short_threshold, level, provider)

    def init_factors(self, entity_ids, entity_type, exchanges, codes, the_timestamp, start_timestamp,
                     end_timestamp):
        bull_factor = BullFactor(entity_ids=entity_ids, entity_type=entity_type, exchanges=exchanges,
                                 codes=codes, the_timestamp=the_timestamp, start_timestamp=start_timestamp,
                                 end_timestamp=end_timestamp, provider='joinquant', level=self.level, auto_load=True)

        self.filter_factors = [bull_factor]


if __name__ == '__main__':
    s = TechnicalSelector(codes=SAMPLE_STOCK_CODES, start_timestamp='2018-01-01', end_timestamp='2019-06-30')
    s.run()
    s.draw()
