# -*- coding: utf-8 -*-
from zvt.domain import BalanceSheet
from zvt.factors import GoodCompanyFactor
from zvt.factors.target_selector import TargetSelector


class FundamentalSelector(TargetSelector):
    def init_factors(self, entity_ids, entity_schema, exchanges, codes, the_timestamp, start_timestamp, end_timestamp,
                     level):
        # 核心资产=(高ROE 高现金流 高股息 低应收 低资本开支 低财务杠杆 有增长)
        # 高roe 高现金流 低财务杠杆 有增长
        factor1 = GoodCompanyFactor(entity_ids=entity_ids, codes=codes, the_timestamp=the_timestamp,
                                    start_timestamp=start_timestamp, end_timestamp=end_timestamp, provider='eastmoney')

        self.filter_factors.append(factor1)

        # 高股息 低应收
        factor2 = GoodCompanyFactor(data_schema=BalanceSheet, entity_ids=entity_ids, codes=codes,
                                    the_timestamp=the_timestamp,
                                    columns=[BalanceSheet.accounts_receivable],
                                    filters=[
                                        BalanceSheet.accounts_receivable <= 0.3 * BalanceSheet.total_current_assets],
                                    start_timestamp=start_timestamp, end_timestamp=end_timestamp, provider='eastmoney',
                                    col_period_threshold=None)
        self.filter_factors.append(factor2)


if __name__ == '__main__':
    selector: TargetSelector = FundamentalSelector(start_timestamp='2015-01-01', end_timestamp='2019-06-30')
    selector.run()
    print(selector.get_targets('2019-06-30'))
