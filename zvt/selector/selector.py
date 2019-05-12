import operator
from itertools import accumulate
from typing import List

import pandas as pd
from pandas import DataFrame

from zvt.domain import SecurityType
from zvt.factors.factor import MustFactor, ScoreFactor
from zvt.utils.pd_utils import index_df_with_time


class Selected(object):
    def __init__(self, security_id, score) -> None:
        self.security_id = security_id
        self.score = score


class TargetSelector(object):
    def __init__(self, security_type=SecurityType.stock, exchanges=['sh', 'sz'], codes=None, the_timestamp=None,
                 start_timestamp=None,
                 end_timestamp=None,
                 threshold=0.8) -> None:
        self.security_type = security_type
        self.exchanges = exchanges
        self.codes = codes
        self.the_timestamp = the_timestamp
        self.start_timestamp = start_timestamp
        self.end_timestamp = end_timestamp
        self.threshold = threshold

        self.must_factors: List[MustFactor] = None
        self.score_factors: List[ScoreFactor] = None
        self.must_result = None
        self.score_result = None
        self.result = None
        # a timestamp index DataFrame with columns 'selected'
        self.df: DataFrame = None

        self.init_factors(security_type=security_type, exchanges=exchanges, codes=codes, the_timestamp=the_timestamp,
                          start_timestamp=start_timestamp, end_timestamp=end_timestamp)

    def init_factors(self, security_type, exchanges, codes, the_timestamp, start_timestamp, end_timestamp):
        raise NotImplementedError

    def run(self):
        if self.must_factors:
            musts = []
            for factor in self.must_factors:
                df = factor.get_df()
                if len(df.columns) > 1:
                    musts.append(df.agg("and", axis="columns"))
                else:
                    musts.append(df)

            self.must_result = list(accumulate(musts, func=operator.__and__))[-1]

        if self.score_factors:
            scores = []
            for factor in self.score_factors:
                df = factor.get_df()
                if len(df.columns) > 1:
                    scores.append(df.agg("mean", axis="columns"))
                else:
                    scores.append(df)
            self.score_result = list(accumulate(scores, func=operator.__add__))[-1]

        if (self.must_result is not None) and (self.score_result is not None):
            self.result = self.score_result[self.must_result > 0 and self.score_result > self.threshold]
        elif self.score_result is not None:
            self.result = self.score_result[self.score_result > self.threshold]
        else:
            self.result = self.must_result

        self.result.name = 'score'
        self.df = self.result.reset_index()

        self.df = index_df_with_time(self.df)

        print(self.df)

    def get_targets(self, timestamp) -> pd.DataFrame:
        if timestamp in self.df.index:
            return self.df.loc[timestamp, :]
        else:
            return pd.DataFrame()

    def get_df(self):
        return self.df
