import operator
from itertools import accumulate
from typing import List

import pandas as pd
from pandas import DataFrame

from zvt.domain import SecurityType, TradingLevel
from zvt.factors.factor import MustFactor, ScoreFactor
from zvt.utils.pd_utils import index_df_with_time
from zvt.utils.time_utils import to_pd_timestamp


class TargetSelector(object):
    def __init__(self, security_type=SecurityType.stock, exchanges=['sh', 'sz'], codes=None, the_timestamp=None,
                 start_timestamp=None,
                 end_timestamp=None,
                 threshold=0.8,
                 level=TradingLevel.LEVEL_1DAY,
                 provider='eastmoney') -> None:
        """

        :param security_type:
        :type security_type:
        :param exchanges:
        :type exchanges:
        :param codes:
        :type codes:
        :param the_timestamp:
        :type the_timestamp:
        :param start_timestamp:
        :type start_timestamp:
        :param end_timestamp:
        :type end_timestamp:
        :param threshold:
        :type threshold:
        """
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

        self.must_factors: List[MustFactor] = None
        self.score_factors: List[ScoreFactor] = None
        self.must_result = None
        self.score_result = None
        self.result = None
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
                df = factor.get_df()
                if len(df.columns) > 1:
                    s = df.agg("mean", axis="columns")
                    s.name = 'score'
                    scores.append(s.to_frame(name='score'))
                else:
                    df.columns = ['score']
                    scores.append(df)
            self.score_result = list(accumulate(scores, func=operator.__add__))[-1]

        if (self.must_result is not None) and (self.score_result is not None):
            self.result = self.score_result[self.must_result.score and (self.score_result.score >= self.threshold)]
        elif self.score_result is not None:
            self.result = self.score_result[self.score_result.score >= self.threshold]
        else:
            self.result = self.must_result[self.must_result.score]

        self.df = self.result.reset_index()

        self.df = index_df_with_time(self.df)

    def get_targets(self, timestamp) -> pd.DataFrame:
        if timestamp in self.df.index:
            return self.df.loc[[timestamp], :]
        else:
            return pd.DataFrame()

    def get_df(self):
        return self.df
