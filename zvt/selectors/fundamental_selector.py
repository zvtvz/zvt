# -*- coding: utf-8 -*-
from zvt.factors.fundamental_factor import GoodCompanyFactor
from zvt.selectors.selector import TargetSelector


class FundamentalSelector(TargetSelector):
    def init_factors(self, entity_ids, entity_type, exchanges, codes, the_timestamp, start_timestamp,
                     end_timestamp):
        factor = GoodCompanyFactor(entity_ids=entity_ids, codes=codes, the_timestamp=the_timestamp,
                                   start_timestamp=start_timestamp,
                                   end_timestamp=end_timestamp, keep_all_timestamp=True, provider=self.provider,
                                   auto_load=True, time_field='timestamp')
        self.filter_factors.append(factor)


if __name__ == '__main__':
    selector: TargetSelector = FundamentalSelector(start_timestamp='2000-01-01', end_timestamp='2019-06-30')
    selector.run()
    selector.draw()
