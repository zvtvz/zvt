# -*- coding: utf-8 -*-
from examples.factors.technical_selector import TechnicalSelector
from zvdata import now_pd_timestamp, IntervalLevel
from zvt.api import get_blocks
from zvt.factors import IndexMoneyFlowFactor
from zvt.factors.target_selector import TargetSelector
from zvt.settings import SAMPLE_STOCK_CODES


class IndexSelector(TargetSelector):

    def __init__(self, entity_ids=None, entity_type='stock', exchanges=['sh', 'sz'], codes=None, the_timestamp=None,
                 start_timestamp=None, end_timestamp=None, long_threshold=0.8, short_threshold=0.2,
                 level=IntervalLevel.LEVEL_1DAY, provider='sina', block_selector=None) -> None:
        super().__init__(entity_ids, entity_type, exchanges, codes, the_timestamp, start_timestamp, end_timestamp,
                         long_threshold, short_threshold, level, provider, block_selector)

    def init_factors(self, entity_ids, entity_type, exchanges, codes, the_timestamp, start_timestamp, end_timestamp,
                     level):
        index_factor = IndexMoneyFlowFactor(start_timestamp=start_timestamp, end_timestamp=end_timestamp, level=level,
                                            provider='sina', codes=codes)
        self.score_factors.append(index_factor)


if __name__ == '__main__':
    df = get_blocks(provider='sina', block_category='industry')

    index_selector = IndexSelector(entity_type='index', exchanges=None, start_timestamp='2019-01-01',
                                   end_timestamp=now_pd_timestamp(), codes=df['code'].to_list())
    index_selector.run()

    # index_selector.draw()

    s = TechnicalSelector(codes=SAMPLE_STOCK_CODES, start_timestamp='2019-01-01', end_timestamp='2019-06-30',
                          block_selector=index_selector)
    s.run()
    s.draw()
