# -*- coding: utf-8 -*-
from zvdata import now_pd_timestamp
from zvt.factors import IndexMoneyFlowFactor
from zvt.factors.target_selector import TargetSelector


class IndexSelector(TargetSelector):
    def init_factors(self, entity_ids, entity_type, exchanges, codes, the_timestamp, start_timestamp, end_timestamp,
                     level):
        index_factor = IndexMoneyFlowFactor(start_timestamp=start_timestamp, end_timestamp=end_timestamp, level=level)
        self.score_factors.append(index_factor)


if __name__ == '__main__':
    index_selector = IndexSelector(entity_type='index', exchanges=None, start_timestamp='2019-01-01',
                                   end_timestamp=now_pd_timestamp())
    index_selector.run()

    index_selector.draw()
