# -*- coding: utf-8 -*-
from zvt.contract import IntervalLevel
from zvt.domain import Stock
from zvt.factors.target_selector import TargetSelector
from zvt.factors.technical_factor import BullFactor
from zvt.consts import SAMPLE_STOCK_CODES


class TechnicalSelector(TargetSelector):

    def __init__(self, entity_ids=None, entity_schema=Stock, exchanges=['sh', 'sz'], codes=None, the_timestamp=None,
                 start_timestamp=None, end_timestamp=None, long_threshold=0.8, short_threshold=0.2,
                 level=IntervalLevel.LEVEL_1DAY, provider='joinquant') -> None:
        super().__init__(entity_ids, entity_schema, exchanges, codes, the_timestamp, start_timestamp, end_timestamp,
                         long_threshold, short_threshold, level, provider)

    def init_factors(self, entity_ids, entity_schema, exchanges, codes, the_timestamp, start_timestamp, end_timestamp,
                     level):
        bull_factor = BullFactor(entity_ids=entity_ids, entity_schema=entity_schema, exchanges=exchanges,
                                 codes=codes, the_timestamp=the_timestamp, start_timestamp=start_timestamp,
                                 end_timestamp=end_timestamp, provider='joinquant', level=level)

        self.add_filter_factor(bull_factor)


if __name__ == '__main__':
    s = TechnicalSelector(codes=SAMPLE_STOCK_CODES, start_timestamp='2018-01-01', end_timestamp='2019-06-30')
    s.run()
    s.draw()
