# -*- coding: utf-8 -*-
from zvt.factors import GoodCompanyFactor
from zvt.factors.target_selector import TargetSelector


class FundamentalSelector(TargetSelector):
    def init_factors(self, entity_ids, entity_type, exchanges, codes, the_timestamp, start_timestamp, end_timestamp,
                     level):
        # 高roe 有增长
        factor = GoodCompanyFactor(entity_ids=entity_ids, codes=codes, the_timestamp=the_timestamp,
                                   start_timestamp=start_timestamp, end_timestamp=end_timestamp, provider='eastmoney')
        self.filter_factors.append(factor)


if __name__ == '__main__':
    selector: TargetSelector = FundamentalSelector(start_timestamp='2000-01-01', end_timestamp='2019-06-30')
    selector.run()
    selector.draw()
