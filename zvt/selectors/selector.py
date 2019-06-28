import operator
from itertools import accumulate
from typing import List

import pandas as pd
from pandas import DataFrame

from zvt.domain import SecurityType, TradingLevel
from zvt.factors.factor import FilterFactor, ScoreFactor
from zvt.utils.pd_utils import index_df, df_is_not_null
from zvt.utils.time_utils import to_pd_timestamp


class TargetSelector(object):
    def __init__(self,
                 security_list=None,
                 security_type=SecurityType.stock,
                 exchanges=['sh', 'sz'],
                 codes=None,
                 the_timestamp=None,
                 start_timestamp=None,
                 end_timestamp=None,
                 threshold=0.8,
                 level=TradingLevel.LEVEL_1DAY,
                 provider='eastmoney') -> None:
        self.security_list = security_list
        self.security_type = security_type
        self.exchanges = exchanges
        self.codes = codes
        self.provider = provider

        if the_timestamp:
            self.the_timestamp = to_pd_timestamp(the_timestamp)
            self.start_timestamp = self.the_timestamp
            self.end_timestamp = self.the_timestamp
        elif start_timestamp and end_timestamp:
            self.start_timestamp = to_pd_timestamp(start_timestamp)
            self.end_timestamp = to_pd_timestamp(end_timestamp)
        else:
            assert False

        self.threshold = threshold
        self.level = level

        self.filter_factors: List[FilterFactor] = []
        self.score_factors: List[ScoreFactor] = []
        self.must_result = None
        self.score_result = None
        self.result_df: DataFrame = None

        self.init_factors(security_list=security_list, security_type=security_type, exchanges=exchanges, codes=codes,
                          the_timestamp=the_timestamp, start_timestamp=start_timestamp, end_timestamp=end_timestamp)

    def init_factors(self, security_list, security_type, exchanges, codes, the_timestamp, start_timestamp,
                     end_timestamp):
        pass

    def add_filter_factor(self, factor):
        self.filter_factors.append(factor)
        return self

    def add_score_factor(self, factor):
        self.score_factors.append(factor)
        return self

    def move_on(self, to_timestamp=None, kdata_use_begin_time=False, timeout=20):
        if self.score_factors:
            for factor in self.score_factors:
                factor.move_on(to_timestamp, timeout=timeout)
        if self.filter_factors:
            for factor in self.filter_factors:
                factor.move_on(to_timestamp, timeout=timeout)
        self.run()

    def run(self):
        if self.filter_factors:
            musts = []
            for factor in self.filter_factors:
                df = factor.get_result_df()
                if len(df.columns) > 1:
                    s = df.agg("and", axis="columns")
                    s.name = 'score'
                    musts.append(s.to_frame(name='score'))
                else:
                    df.columns = ['score']
                    musts.append(df)

            self.must_result = list(accumulate(musts, func=operator.__and__))[-1]

        if self.score_factors:
            scores = []
            for factor in self.score_factors:
                df = factor.get_result_df()
                if len(df.columns) > 1:
                    s = df.agg("mean", axis="columns")
                    s.name = 'score'
                    scores.append(s.to_frame(name='score'))
                else:
                    df.columns = ['score']
                    scores.append(df)
            self.score_result = list(accumulate(scores, func=operator.__add__))[-1]

        if df_is_not_null(self.must_result) and df_is_not_null(self.score_result):
            result1 = self.must_result[self.must_result.score]
            result2 = self.score_result[self.score_result.score >= self.threshold]
            result = result2.loc[result1.index, :]

        elif df_is_not_null(self.score_result):
            result = self.score_result[self.score_result.score >= self.threshold]
        else:
            result = self.must_result[self.must_result.score]

        self.result_df = result.reset_index()

        self.result_df = index_df(self.result_df)

    def get_targets(self, timestamp) -> pd.DataFrame:
        if timestamp in self.result_df.index:
            return self.result_df.loc[[to_pd_timestamp(timestamp)], :]
        else:
            return pd.DataFrame()

    def get_result_df(self):
        return self.result_df
