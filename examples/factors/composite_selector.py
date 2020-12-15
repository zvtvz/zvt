# -*- coding: utf-8 -*-
from examples.factors.technical_selector import TechnicalSelector
from zvt.contract import IntervalLevel
from zvt.domain import Block
from zvt.factors.technical import BlockMoneyFlowFactor
from zvt.factors.target_selector import TargetSelector
from zvt.consts import SAMPLE_STOCK_CODES


class BlockSelector(TargetSelector):

    def __init__(self, entity_ids=None, entity_schema=Block, exchanges=None, codes=None, the_timestamp=None,
                 start_timestamp=None, end_timestamp=None, long_threshold=0.8, short_threshold=0.2,
                 level=IntervalLevel.LEVEL_1DAY, provider='sina') -> None:
        super().__init__(entity_ids, entity_schema, exchanges, codes, the_timestamp, start_timestamp, end_timestamp,
                         long_threshold, short_threshold, level, provider)

    def init_factors(self, entity_ids, entity_schema, exchanges, codes, the_timestamp, start_timestamp, end_timestamp,
                     level):
        block_factor = BlockMoneyFlowFactor(start_timestamp=start_timestamp, end_timestamp=end_timestamp,
                                            provider='sina')
        self.score_factors.append(block_factor)


if __name__ == '__main__':
    block_selector = BlockSelector(start_timestamp='2019-01-01')
    block_selector.run()

    # index_selector.draw()

    s = TechnicalSelector(codes=SAMPLE_STOCK_CODES, start_timestamp='2019-01-01', end_timestamp='2019-06-30',
                          block_selector=block_selector)
    s.run()
    s.draw()
