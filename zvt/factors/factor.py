# -*- coding: utf-8 -*-
import logging
import time

import pandas as pd

from zvt.api.common import get_data
from zvt.domain import SecurityType, TradingLevel
from zvt.utils.pd_utils import index_df_with_security_time
from zvt.utils.time_utils import to_pd_timestamp, now_pd_timestamp


class Factor(object):
    logger = logging.getLogger(__name__)

    def __init__(self, security_list=None, security_type=SecurityType.stock, exchanges=['sh', 'sz'], codes=None,
                 the_timestamp=None,
                 start_timestamp=None, end_timestamp=None, keep_all_timestamp=False, fill_method='ffill',
                 effective_number=10) -> None:
        self.factor_name = type(self).__name__.lower()

        if the_timestamp:
            self.the_timestamp = to_pd_timestamp(the_timestamp)
            self.start_timestamp = self.the_timestamp
            self.end_timestamp = self.the_timestamp
        elif start_timestamp and end_timestamp:
            self.start_timestamp = to_pd_timestamp(start_timestamp)
            self.end_timestamp = to_pd_timestamp(end_timestamp)
        else:
            assert False

        self.keep_all_timestamp = keep_all_timestamp
        self.fill_method = fill_method
        self.effective_number = effective_number

        self.security_list = security_list
        self.security_type = security_type
        self.exchanges = exchanges
        self.codes = codes

        self.data_df: pd.DataFrame = None
        self.df: pd.DataFrame = None

    def run(self):
        """
        implement this to calculate factors normalize to [0,1]

        """
        raise NotImplementedError

    def move_on(self, to_timestamp, touching_timestamp):
        """
        when data_df change for realtime refresh

        """
        raise NotImplementedError

    def __repr__(self) -> str:
        return self.data_df.__repr__()

    def get_df(self):
        return self.df

    def get_data_df(self):
        return self.data_df

    def fill_gap(self):
        if self.keep_all_timestamp:
            idx = pd.date_range(self.start_timestamp, self.end_timestamp)
            new_index = pd.MultiIndex.from_product([self.df.index.levels[0], idx],
                                                   names=['security_id', 'timestamp'])
            self.df = self.df.reindex(new_index)
            self.df = self.df.fillna(method=self.fill_method, limit=self.effective_number)


class MustFactor(Factor):
    pass


class ScoreFactor(Factor):
    pass


class StateFactor(Factor):
    states = []

    def get_state(self, timestamp, security_id):
        pass


class OneSchemaFactor(Factor):
    def __init__(self, data_schema, security_list=None, security_type=SecurityType.stock, exchanges=['sh', 'sz'],
                 codes=None,
                 the_timestamp=None, start_timestamp=None, end_timestamp=None, keep_all_timestamp=False,
                 fill_method='ffill', columns=[], filters=None, provider='eastmoney',
                 level=TradingLevel.LEVEL_1DAY, effective_number=10) -> None:
        super().__init__(security_list, security_type, exchanges, codes, the_timestamp, start_timestamp, end_timestamp,
                         keep_all_timestamp, fill_method, effective_number)

        self.data_schema = data_schema

        if columns:
            self.columns = set(columns) | {self.data_schema.security_id, self.data_schema.timestamp}
            self.factors = [item.key for item in columns]
        else:
            self.columns = None

        self.provider = provider
        self.level = level
        self.filters = filters

        # use security_list if possible
        if self.security_list:
            self.original_df = get_data(data_schema=self.data_schema, security_list=self.security_list,
                                        provider=self.provider,
                                        columns=self.columns, start_timestamp=self.start_timestamp,
                                        end_timestamp=self.end_timestamp, filters=self.filters, level=self.level)
        else:
            self.original_df = get_data(data_schema=self.data_schema, codes=self.codes,
                                        provider=self.provider,
                                        columns=self.columns, start_timestamp=self.start_timestamp,
                                        end_timestamp=self.end_timestamp, filters=self.filters, level=self.level)

        if self.original_df is None or self.original_df.empty:
            raise Exception(
                'no data for: {} {} level:{} from: {} to: {}'.format(self.security_list, self.codes,
                                                                     self.level,
                                                                     self.start_timestamp,
                                                                     self.end_timestamp))
        self.original_df = index_df_with_security_time(self.original_df)

        self.logger.info('factor:{},original_df:\n{}'.format(self.factor_name, self.original_df))

    def depth_computing(self):
        self.logger.info('do nothing for depth_computing')

    def breadth_computing(self):
        self.logger.info('do nothing for breadth_computing')

    def run(self):
        self.depth_computing()
        self.breadth_computing()

    def move_on(self, to_timestamp, touching_timestamp):
        df = self.original_df.reset_index(level='timestamp')
        recorded_timestamps = df.groupby(level=0)['timestamp'].max()

        self.logger.info('current_timestamps:\n{}'.format(recorded_timestamps))

        for security_id, recorded_timestamp in recorded_timestamps.iteritems():
            while True:
                now_timestamp = now_pd_timestamp()
                if touching_timestamp > now_timestamp:
                    delta = (touching_timestamp - now_timestamp).seconds
                    self.logger.info(
                        'want to get {} {} kdata for {},now is:{},waiting:{}sencods'.format(to_timestamp,
                                                                                            touching_timestamp,
                                                                                            security_id,
                                                                                            now_timestamp, delta))
                    time.sleep(delta)

                added = get_data(data_schema=self.data_schema, provider=self.provider, security_id=security_id,
                                 columns=self.columns, start_timestamp=recorded_timestamp,
                                 end_timestamp=to_timestamp, filters=self.filters, level=self.level)

                if (added is not None) and not added.empty:
                    would_added = added[added['timestamp'] != recorded_timestamp]
                    if not would_added.empty:
                        would_added = index_df_with_security_time(would_added)
                        self.logger.info('would_added:\n{}'.format(would_added))

                        self.original_df = self.original_df.append(would_added)
                        self.original_df = self.original_df.sort_index(level=[0, 1])
                        self.on_data_added(security_id=security_id, size=len(would_added))
                        break
                    else:
                        self.logger.info(
                            'touching_timestamp:{} now_timestamp:{} kdata for {} not ready'.format(touching_timestamp,
                                                                                                   now_pd_timestamp(),
                                                                                                   security_id))

                if now_timestamp > touching_timestamp + pd.Timedelta(seconds=self.level.to_second() / 2):
                    self.logger.warning(
                        'now_timestamp:{},still could not get {} {} kdata for {}'.format(now_timestamp, to_timestamp,
                                                                                         touching_timestamp,
                                                                                         security_id))
                    break

    def on_data_added(self, security_id, size):
        self.logger.info('on_data_added:{} \n {}'.format(security_id, size))


class OneSchemaMustFactor(OneSchemaFactor, MustFactor):
    def __init__(self, data_schema, security_list=None, security_type=SecurityType.stock, exchanges=['sh', 'sz'],
                 codes=None,
                 the_timestamp=None, start_timestamp=None, end_timestamp=None, keep_all_timestamp=False,
                 fill_method='ffill', columns=[], filters=None, provider='eastmoney', level=TradingLevel.LEVEL_1DAY,
                 effective_number=10) -> None:
        super().__init__(data_schema, security_list, security_type, exchanges, codes, the_timestamp, start_timestamp,
                         end_timestamp, keep_all_timestamp, fill_method, columns, filters, provider, level,
                         effective_number)


class OneSchemaScoreFactor(OneSchemaFactor, ScoreFactor):
    def __init__(self, data_schema, security_list=None, security_type=SecurityType.stock, exchanges=['sh', 'sz'],
                 codes=None, the_timestamp=None, start_timestamp=None, end_timestamp=None, keep_all_timestamp=False,
                 fill_method='ffill', columns=[], filters=None, provider='eastmoney', level=TradingLevel.LEVEL_1DAY,
                 effective_number=10,
                 depth_computing_method='ma',
                 depth_computing_param={'window': '100D', 'on': 'timestamp'},
                 breadth_computing_method='quantile',
                 breadth_computing_param={'score_levels': [0.1, 0.3, 0.5, 0.7, 0.9]}) -> None:
        super().__init__(data_schema, security_list, security_type, exchanges, codes, the_timestamp, start_timestamp,
                         end_timestamp, keep_all_timestamp, fill_method, columns, filters, provider, level,
                         effective_number)
        self.depth_computing_method = depth_computing_method
        self.depth_computing_param = depth_computing_param

        self.breadth_computing_method = breadth_computing_method
        self.breadth_computing_param = breadth_computing_param

    def depth_computing(self):
        self.data_df = self.original_df.reset_index(level='timestamp')

        if self.depth_computing_method == 'ma':
            window = self.depth_computing_param['window']

            on = self.depth_computing_param['on']

            if on == 'timestamp':
                if isinstance(window, pd.DateOffset):
                    window = '{}D'.format(self.window.days)

                self.data_df = self.data_df.groupby(level=0).rolling(window=window,
                                                                     on='timestamp').mean()
            else:
                assert type(window) == int
                self.data_df = self.data_df.groupby(level=0).rolling(window=window).mean()
        elif self.depth_computing_method == 'count':
            window = self.depth_computing_param['window']
            if isinstance(window, pd.DateOffset):
                window = '{}D'.format(self.window.days)

            self.data_df = self.data_df.groupby(level=0).rolling(window=window, on='timestamp').count()

        self.data_df = self.data_df.reset_index(level=0, drop=True)
        self.data_df = self.data_df.set_index('timestamp', append=True)

        self.data_df = self.data_df.loc[(slice(None), slice(self.start_timestamp, self.end_timestamp)), :]

        self.logger.info('factor:{},data_df:\n{}'.format(self.factor_name, self.data_df))

    def breadth_computing(self):
        if self.breadth_computing_method == 'quantile':
            self.score_levels = self.breadth_computing_param['score_levels']
            self.score_levels.sort(reverse=True)

            self.quantile = self.data_df.groupby(level=1).quantile(self.score_levels)
            self.quantile.index.names = ['timestamp', 'score']

            self.logger.info('factor:{},quantile:\n{}'.format(self.factor_name, self.quantile))

            self.df = self.data_df.copy()
            self.df.reset_index(inplace=True, level='security_id')
            self.df['quantile'] = None
            for timestamp in self.quantile.index.levels[0]:
                length = len(self.df.loc[self.df.index == timestamp, 'quantile'])
                self.df.loc[self.df.index == timestamp, 'quantile'] = [self.quantile.loc[timestamp].to_dict()] * length

            self.logger.info('factor:{},df with quantile:\n{}'.format(self.factor_name, self.df))

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

            self.df = self.df.loc[~self.df.index.duplicated(keep='first')]

            self.logger.info('factor:{},df:\n{}'.format(self.factor_name, self.df))

            self.fill_gap()

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
