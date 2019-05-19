# -*- coding: utf-8 -*-
import logging

import pandas as pd

from zvt.api.common import get_data
from zvt.domain import SecurityType
from zvt.utils.pd_utils import index_df_with_security_time
from zvt.utils.time_utils import to_pd_timestamp


class Factor(object):
    logger = logging.getLogger(__name__)
    df: pd.DataFrame = None

    def __init__(self, security_type=SecurityType.stock, exchanges=['sh', 'sz'], codes=None, the_timestamp=None,
                 window=None, window_func='mean', start_timestamp=None, end_timestamp=None, keep_all_timestamp=False,
                 fill_method='ffill') -> None:
        """

        :param keep_all_timestamp:
        :type keep_all_timestamp:
        :param fill_method:
        :type fill_method:
        :param security_type:
        :type security_type:
        :param exchanges:
        :type exchanges:
        :param codes:
        :type codes:
        :param the_timestamp:the specific timestamp for the factor
        :type the_timestamp:
        :param window: time window for the factor
        :type window: pd.DateOffset
        :param start_timestamp:
        :type start_timestamp:
        :param end_timestamp:
        :type end_timestamp:
        """
        if the_timestamp:
            self.the_timestamp = to_pd_timestamp(the_timestamp)
            self.start_timestamp = self.the_timestamp
            self.end_timestamp = self.the_timestamp
        elif start_timestamp and end_timestamp:
            self.start_timestamp = to_pd_timestamp(start_timestamp)
            self.end_timestamp = to_pd_timestamp(end_timestamp)
        else:
            assert False

        self.window = window
        self.window_func = window_func
        self.keep_all_timestamp = keep_all_timestamp
        self.fill_method = fill_method

        if self.window:
            self.fetch_start_timestamp = self.start_timestamp - self.window
        else:
            self.fetch_start_timestamp = self.start_timestamp

        self.security_type = security_type
        self.exchanges = exchanges
        self.codes = codes

    def run(self):
        """
        implement this to calculate factors normalize to [0,1]

        """
        raise NotImplementedError

    def __repr__(self) -> str:
        return self.df.__repr__()

    def get_df(self):
        return self.df

    def fill_gap(self):
        if self.keep_all_timestamp:
            idx = pd.date_range(self.start_timestamp, self.end_timestamp)
            self.df.reindex(idx, method=self.fill_method)


class MustFactor(Factor):
    pass


class ScoreFactor(Factor):
    pass


class OneSchemaFactor(Factor):
    data_schema = None

    def __init__(self, security_type=SecurityType.stock, exchanges=['sh', 'sz'], codes=None, the_timestamp=None,
                 window=None, window_func='mean', start_timestamp=None, end_timestamp=None, keep_all_timestamp=False,
                 fill_method='ffill', columns=[], filters=None, provider='eastmoney') -> None:
        super().__init__(security_type, exchanges, codes, the_timestamp, window, window_func, start_timestamp,
                         end_timestamp, keep_all_timestamp, fill_method)

        self.columns = set(columns) | {self.data_schema.security_id, self.data_schema.timestamp}
        self.factors = [item.key for item in columns]
        self.provider = provider

        self.original_df = get_data(data_schema=self.data_schema, provider=self.provider, codes=self.codes,
                                    columns=self.columns, start_timestamp=self.fetch_start_timestamp,
                                    end_timestamp=self.end_timestamp, filters=filters)

        self.original_df = index_df_with_security_time(self.original_df)

        self.logger.info(self.original_df)

        if self.window:
            self.data_df = self.original_df.reset_index(level='timestamp')

            # TODO:better way to handle window function
            if self.window_func == 'mean':
                self.data_df = self.data_df.groupby(level=0).rolling(window='{}D'.format(self.window.days),
                                                                     on='timestamp').mean()
            elif self.window_func == 'count':
                self.data_df = self.data_df.groupby(level=0).rolling(window='{}D'.format(self.window.days),
                                                                     on='timestamp').count()
            self.data_df = self.data_df.reset_index(level=0, drop=True)
            self.data_df = self.data_df.set_index('timestamp', append=True)
            print(self.data_df)
        else:
            self.data_df = self.original_df

        self.data_df = self.data_df.loc[(slice(None), slice(self.start_timestamp, self.end_timestamp)), :]

        self.logger.info(self.data_df)


class OneSchemaMustFactor(OneSchemaFactor, MustFactor):

    def __init__(self, security_type=SecurityType.stock, exchanges=['sh', 'sz'], codes=None, the_timestamp=None,
                 window=None, window_func='mean', start_timestamp=None, end_timestamp=None, keep_all_timestamp=False,
                 fill_method='ffill', columns=[], filters=None, provider='eastmoney') -> None:
        super().__init__(security_type, exchanges, codes, the_timestamp, window, window_func, start_timestamp,
                         end_timestamp, keep_all_timestamp, fill_method, columns, filters, provider=provider)


class OneSchemaScoreFactor(OneSchemaFactor, ScoreFactor):
    def __init__(self, security_type=SecurityType.stock, exchanges=['sh', 'sz'], codes=None, the_timestamp=None,
                 window=None, window_func='mean', start_timestamp=None, end_timestamp=None, keep_all_timestamp=False,
                 fill_method='ffill', columns=[], filters=None, provider='eastmoney',
                 score_levels=[0.1, 0.3, 0.5, 0.7, 0.9]) -> None:
        super().__init__(security_type, exchanges, codes, the_timestamp, window, window_func, start_timestamp,
                         end_timestamp, keep_all_timestamp, fill_method, columns, filters, provider)
        self.score_levels = score_levels
        self.score_levels.sort(reverse=True)

    @staticmethod
    def norm_score(factors, quantile, timestamp, score_levels):
        for col in factors.index:
            min_score = score_levels[-1]

            if factors[col] < quantile.loc[timestamp, min_score][col]:
                factors[col] = 0
                continue

            for score in score_levels[:-1]:
                if factors[col] >= quantile.loc[timestamp, score][col]:
                    factors[col] = score
                    continue

    def run(self):
        self.quantile = self.data_df.groupby(level=1).quantile(self.score_levels)
        self.quantile.index.names = ['timestamp', 'score']

        self.logger.info(self.quantile)

        self.df = self.data_df.copy()
        self.df.reset_index(inplace=True, level='security_id')
        self.df['quantile'] = None
        for timestamp in self.quantile.index.levels[0]:
            length = len(self.df.loc[self.df.index == timestamp, 'quantile'])
            self.df.loc[self.df.index == timestamp, 'quantile'] = [self.quantile.loc[timestamp].to_dict()] * length

        self.logger.info(self.df)

        # self.df = self.df.set_index(['security_id'], append=True)
        # self.df = self.df.sort_index(level=[0, 1])
        #
        # self.logger.info(self.df)
        #
        def calculate_score(df, factor_name, quantile):
            original_value = df[factor_name]
            score_map = quantile.get(factor_name)
            min_score = self.score_levels[-1]

            if original_value < score_map.get(min_score):
                return 0

            for score in self.score_levels[:-1]:
                if original_value >= score_map.get(score):
                    return score

        for factor in self.factors:
            self.df[factor] = self.df.apply(lambda x: calculate_score(x, factor, x['quantile']), axis=1)

        self.df = self.df.reset_index()
        self.df = index_df_with_security_time(self.df)
        self.df = self.df.loc[:, self.factors]

        self.logger.info(self.df)

        self.fill_gap()


class StateFactor(Factor):
    states = []

    def get_state(self, timestamp, security_id):
        pass
