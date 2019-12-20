# -*- coding: utf-8 -*-
import operator
from itertools import accumulate
from typing import List, Union

import pandas as pd

from zvdata import IntervalLevel
from zvdata.utils.pd_utils import normal_index_df
from zvdata.utils.time_utils import now_pd_timestamp
from zvt.domain import FinanceFactor, IndexMoneyFlow
from zvt.factors import Transformer, Accumulator
from zvt.factors.algorithm import Scorer, RankScorer
from zvt.factors.factor import Factor, ScoreFactor


class FinanceBaseFactor(Factor):
    def __init__(self,
                 data_schema=FinanceFactor,
                 entity_ids: List[str] = None,
                 entity_type: str = 'stock',
                 exchanges: List[str] = ['sh', 'sz'],
                 codes: List[str] = None,
                 the_timestamp: Union[str, pd.Timestamp] = None,
                 start_timestamp: Union[str, pd.Timestamp] = None,
                 end_timestamp: Union[str, pd.Timestamp] = None,
                 columns: List = None, filters: List = None,
                 order: object = None,
                 limit: int = None,
                 provider: str = 'eastmoney',
                 level: Union[str, IntervalLevel] = IntervalLevel.LEVEL_1DAY,
                 category_field: str = 'entity_id',
                 time_field: str = 'timestamp',
                 computing_window: int = None,
                 keep_all_timestamp: bool = False,
                 fill_method: str = 'ffill',
                 effective_number: int = None,
                 transformer: Transformer = None,
                 accumulator: Accumulator = None,
                 persist_factor: bool = False,
                 dry_run: bool = False) -> None:
        if not columns:
            columns = data_schema.important_cols()

        super().__init__(data_schema, entity_ids, entity_type, exchanges, codes, the_timestamp, start_timestamp,
                         end_timestamp, columns, filters, order, limit, provider, level, category_field, time_field,
                         computing_window, keep_all_timestamp, fill_method, effective_number, transformer, accumulator,
                         persist_factor, dry_run)


class GoodCompanyFactor(FinanceBaseFactor):
    def __init__(self, data_schema=FinanceFactor,
                 entity_ids: List[str] = None,
                 entity_type: str = 'stock',
                 exchanges: List[str] = ['sh', 'sz'],
                 codes: List[str] = None,
                 the_timestamp: Union[str, pd.Timestamp] = None,
                 start_timestamp: Union[str, pd.Timestamp] = '2005-01-01',
                 end_timestamp: Union[str, pd.Timestamp] = now_pd_timestamp(),
                 # 高roe,高现金流,低财务杠杆，有增长
                 columns: List = [FinanceFactor.roe,
                                  FinanceFactor.op_income_growth_yoy,
                                  FinanceFactor.net_profit_growth_yoy,
                                  FinanceFactor.report_period,
                                  FinanceFactor.op_net_cash_flow_per_op_income,
                                  FinanceFactor.sales_net_cash_flow_per_op_income,
                                  FinanceFactor.current_ratio,
                                  FinanceFactor.debt_asset_ratio],
                 filters: List = [FinanceFactor.roe >= 0.02,
                                  FinanceFactor.op_income_growth_yoy >= 0.05,
                                  FinanceFactor.net_profit_growth_yoy >= 0.05,
                                  FinanceFactor.op_net_cash_flow_per_op_income >= 0.1,
                                  FinanceFactor.sales_net_cash_flow_per_op_income >= 0.3,
                                  FinanceFactor.current_ratio >= 1,
                                  FinanceFactor.debt_asset_ratio <= 0.5],
                 order: object = None,
                 limit: int = None,
                 provider: str = 'eastmoney',
                 level: Union[str, IntervalLevel] = IntervalLevel.LEVEL_1DAY,
                 category_field: str = 'entity_id',
                 time_field: str = 'timestamp',
                 computing_window: int = None,
                 keep_all_timestamp: bool = True,
                 fill_method: str = 'ffill',
                 effective_number: int = None,
                 transformer: Transformer = None,
                 accumulator: Accumulator = None,
                 persist_factor: bool = False,
                 dry_run: bool = False,
                 # 3 years
                 window='1095d',
                 count=8,
                 col_threshold={'roe': 0.02},
                 handling_on_period=('roe',)) -> None:
        self.window = window
        self.count = count
        self.col_threshold = col_threshold
        # 对于根据年度计算才有意义的指标，比如roe,我们会对不同季度的值区别处理
        self.handling_on_period = handling_on_period

        super().__init__(data_schema, entity_ids, entity_type, exchanges, codes, the_timestamp, start_timestamp,
                         end_timestamp, columns, filters, order, limit, provider, level, category_field, time_field,
                         computing_window, keep_all_timestamp, fill_method, effective_number, transformer, accumulator,
                         persist_factor, dry_run)

    def do_compute(self):
        def filter_df(df):
            se = pd.Series(index=df.index)
            for index, row in df.iterrows():

                if row.report_period == 'year':
                    mul = 4
                elif row.report_period == 'season3':
                    mul = 3
                elif row.report_period == 'half_year':
                    mul = 2
                else:
                    mul = 1

                filters = []
                for col in self.col_threshold:
                    col_se = eval(f'row.{col}')
                    if col in self.handling_on_period:
                        filters.append(col_se >= mul * self.col_threshold[col])
                    else:
                        filters.append(col_se >= self.col_threshold[col])
                se[index] = list(accumulate(filters, func=operator.__and__))[-1]

            return se

        self.factor_df = self.data_df.loc[lambda df: filter_df(df), :]

        self.factor_df = pd.DataFrame(index=self.data_df.index, columns=['count'], data=1)

        self.factor_df = self.factor_df.reset_index(level=1)

        self.factor_df = self.factor_df.groupby(level=0).rolling(window=self.window, on=self.time_field).count()

        self.factor_df = self.factor_df.reset_index(level=0, drop=True)
        self.factor_df = self.factor_df.set_index(self.time_field, append=True)

        self.factor_df = self.factor_df.loc[(slice(None), slice(self.start_timestamp, self.end_timestamp)), :]

        self.logger.info('factor:{},factor_df:\n{}'.format(self.factor_name, self.factor_df))

        self.result_df = self.factor_df.apply(lambda x: x >= self.count)

        self.logger.info('factor:{},result_df:\n{}'.format(self.factor_name, self.result_df))


class IndexMoneyFlowFactor(ScoreFactor):
    def __init__(self,
                 codes=None,
                 the_timestamp: Union[str, pd.Timestamp] = None,
                 start_timestamp: Union[str, pd.Timestamp] = None,
                 end_timestamp: Union[str, pd.Timestamp] = None,
                 columns: List = [IndexMoneyFlow.net_inflows, IndexMoneyFlow.net_inflow_rate,
                                  IndexMoneyFlow.net_main_inflows, IndexMoneyFlow.net_main_inflow_rate],
                 filters: List = [],
                 order: object = None,
                 limit: int = None,
                 provider: str = 'sina',
                 level: Union[str, IntervalLevel] = IntervalLevel.LEVEL_1DAY,
                 category_field: str = 'entity_id',
                 time_field: str = 'timestamp',
                 keep_all_timestamp: bool = False,
                 fill_method: str = 'ffill',
                 effective_number: int = 10,
                 scorer: Scorer = RankScorer(ascending=True)) -> None:
        super().__init__(IndexMoneyFlow, None, 'index', None, codes, the_timestamp, start_timestamp,
                         end_timestamp, columns, filters, order, limit, provider, level, category_field, time_field,
                         keep_all_timestamp, fill_method, effective_number, scorer)

    def do_compute(self):
        self.pipe_df = self.data_df.copy()
        self.pipe_df = self.pipe_df.groupby(level=1).rolling(window=20).mean()
        self.pipe_df = self.pipe_df.reset_index(level=0, drop=True)
        self.pipe_df = self.pipe_df.reset_index()
        self.pipe_df = normal_index_df(self.pipe_df)

        super().do_compute()


if __name__ == '__main__':
    f1 = GoodCompanyFactor(keep_all_timestamp=False)
    print(f1.result_df)
