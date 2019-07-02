import operator
from itertools import accumulate
from typing import List

import pandas as pd
import plotly.graph_objs as go
from pandas import DataFrame

from zvt.charts import Chart
from zvt.domain import SecurityType, TradingLevel
from zvt.factors.factor import FilterFactor, ScoreFactor
from zvt.utils.pd_utils import index_df, df_is_not_null, index_df_with_category_time
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
                 long_threshold=0.8,
                 short_threshold=-0.8,
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

        self.long_threshold = long_threshold
        self.short_threshold = short_threshold
        self.level = level

        self.filter_factors: List[FilterFactor] = []
        self.score_factors: List[ScoreFactor] = []
        self.filter_result = None
        self.score_result = None

        self.open_long_df: DataFrame = None
        self.open_short_df: DataFrame = None
        self.keep_long_df: DataFrame = None
        self.keep_short_df: DataFrame = None

        self.init_factors(security_list=security_list, security_type=security_type, exchanges=exchanges, codes=codes,
                          the_timestamp=the_timestamp, start_timestamp=start_timestamp, end_timestamp=end_timestamp)

    def init_factors(self, security_list, security_type, exchanges, codes, the_timestamp, start_timestamp,
                     end_timestamp):
        pass

    def add_filter_factor(self, factor: FilterFactor):
        self.filter_factors.append(factor)
        return self

    def add_score_factor(self, factor: ScoreFactor):
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
        """

        """
        if self.filter_factors:
            musts = []
            for factor in self.filter_factors:
                df = factor.get_result_df()

                if not df_is_not_null(df):
                    raise Exception('no data for factor:{},{}'.format(factor.factor_name, factor))

                if len(df.columns) > 1:
                    s = df.agg("and", axis="columns")
                    s.name = 'score'
                    musts.append(s.to_frame(name='score'))
                else:
                    df.columns = ['score']
                    musts.append(df)

            self.filter_result = list(accumulate(musts, func=operator.__and__))[-1]

        if self.score_factors:
            scores = []
            for factor in self.score_factors:
                df = factor.get_result_df()
                if not df_is_not_null(df):
                    raise Exception('no data for factor:{],{}'.format(factor.factor_name, factor))

                if len(df.columns) > 1:
                    s = df.agg("mean", axis="columns")
                    s.name = 'score'
                    scores.append(s.to_frame(name='score'))
                else:
                    df.columns = ['score']
                    scores.append(df)
            self.score_result = list(accumulate(scores, func=operator.__add__))[-1]

        self.generate_targets()

    def get_targets(self, timestamp, target_type='open_long') -> pd.DataFrame:
        if target_type == 'open_long':
            df = self.open_long_df
        if target_type == 'open_short':
            df = self.open_short_df
        if target_type == 'keep_long':
            df = self.keep_long_df
        if target_type == 'keep_short':
            df = self.keep_short_df

        if df_is_not_null(df):
            if timestamp in df.index:
                target_df = df.loc[[to_pd_timestamp(timestamp)], :]
                return target_df['security_id'].tolist()
        return []

    def get_open_long_targets(self, timestamp):
        return self.get_targets(timestamp=timestamp, target_type='open_long')

    def get_open_short_targets(self, timestamp):
        return self.get_targets(timestamp=timestamp, target_type='open_short')

    def get_keep_long_targets(self, timestamp):
        return self.get_targets(timestamp=timestamp, target_type='keep_long')

    def get_keep_short_targets(self, timestamp):
        return self.get_targets(timestamp=timestamp, target_type='keep_short')

    # overwrite it to generate targets
    def generate_targets(self):
        if df_is_not_null(self.filter_result) and df_is_not_null(self.score_result):
            # for long
            result1 = self.filter_result[self.filter_result.score]
            result2 = self.score_result[self.score_result.score >= self.long_threshold]
            long_result = result2.loc[result1.index, :]
            # for short
            result1 = self.filter_result[~self.filter_result.score]
            result2 = self.score_result[self.score_result.score <= self.short_threshold]
            short_result = result2.loc[result1.index, :]
        elif df_is_not_null(self.score_result):
            long_result = self.score_result[self.score_result.score >= self.long_threshold]
            short_result = self.score_result[self.score_result.score <= self.short_threshold]
        else:
            long_result = self.filter_result[self.filter_result.score]
            short_result = self.filter_result[~self.filter_result.score]

        self.open_long_df = self.normalize_result_df(long_result)
        self.open_short_df = self.normalize_result_df(short_result)

        # TODO:keep_long,keep_short algorithm

    def get_result_df(self):
        return self.open_long_df

    def normalize_result_df(self, df):
        if df_is_not_null(df):
            df = df.reset_index()
            df = index_df(df)
            df = df.sort_values(by=['score', 'security_id'])
        return df

    def draw(self,
             figures=[go.Table],
             modes=['lines'],
             value_fields=['close'],
             render='html',
             file_name=None,
             width=None,
             height=None,
             title=None,
             keep_ui_state=True,
             annotation_df=None,
             targets='open_long'):

        if targets == 'open_long':
            df = self.open_long_df.copy()
        elif targets == 'open_short':
            df = self.open_long_df.copy()

        df[targets] = targets
        df = df.reset_index()
        df = index_df_with_category_time(df, targets)

        chart = Chart(category_field=targets, figures=figures, modes=modes, value_fields=value_fields,
                      render=render, file_name=file_name,
                      width=width, height=height, title=title, keep_ui_state=keep_ui_state)

        chart.set_data_df(df)
        chart.set_annotation_df(annotation_df)
        return chart.draw()
