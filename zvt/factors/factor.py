# -*- coding: utf-8 -*-
import enum
from typing import List, Union

import pandas as pd
import plotly.graph_objs as go

from zvt.charts import Chart
from zvt.domain import SecurityType, TradingLevel, Provider
from zvt.reader.reader import DataReader, DataListener
from zvt.utils.pd_utils import index_df_with_security_time


class FactorType(enum.Enum):
    filter = 'filter'
    score = 'score'
    state = 'state'


class Factor(DataReader, DataListener):
    factor_type: FactorType = None

    def __init__(self,
                 data_schema: object,
                 security_list: List[str] = None,
                 security_type: Union[str, SecurityType] = SecurityType.stock,
                 exchanges: List[str] = ['sh', 'sz'],
                 codes: List[str] = None,
                 the_timestamp: Union[str, pd.Timestamp] = None,
                 start_timestamp: Union[str, pd.Timestamp] = None,
                 end_timestamp: Union[str, pd.Timestamp] = None,
                 columns: List = None,
                 filters: List = None,
                 provider: Union[str, Provider] = 'eastmoney',
                 level: TradingLevel = TradingLevel.LEVEL_1DAY,
                 real_time: bool = False,
                 refresh_interval: int = 10,
                 category_field: str = 'security_id',
                 # child added arguments
                 keep_all_timestamp: bool = False,
                 fill_method: str = 'ffill',
                 effective_number: int = 10) -> None:
        super().__init__(data_schema, security_list, security_type, exchanges, codes, the_timestamp, start_timestamp,
                         end_timestamp, columns, filters, provider, level, real_time, refresh_interval, category_field)

        self.factor_name = type(self).__name__.lower()

        if columns:
            self.factors = [item.key for item in columns]

        self.keep_all_timestamp = keep_all_timestamp
        self.fill_method = fill_method
        self.effective_number = effective_number

        self.depth_df: pd.DataFrame = None
        self.result_df: pd.DataFrame = None

        self.register_data_listener(self)

    def depth_computing(self):
        self.logger.info('do nothing for depth_computing')

    def breadth_computing(self):
        self.logger.info('do nothing for breadth_computing')

    def compute(self):
        """
        implement this to calculate factors normalize to [0,1]

        """

        self.depth_computing()
        self.breadth_computing()

    def __repr__(self) -> str:
        return self.result_df.__repr__()

    def get_result_df(self):
        return self.result_df

    def get_depth_df(self):
        return self.depth_df

    def draw_depth(self, figures=[go.Scatter], modes=['lines'], value_fields=['close'], render='html', file_name=None,
                   width=None, height=None, title=None, keep_ui_state=True):
        chart = Chart(category_field=self.category_field, figures=figures, modes=modes, value_fields=value_fields,
                      render=render, file_name=file_name,
                      width=width, height=height, title=title, keep_ui_state=keep_ui_state)
        chart.set_data_df(self.depth_df)
        chart.draw()

    def draw_result(self, figures=[go.Scatter], modes=['lines'], value_fields=['score'], render='html', file_name=None,
                    width=None, height=None, title=None, keep_ui_state=True):
        chart = Chart(category_field=self.category_field, figures=figures, modes=modes, value_fields=value_fields,
                      render=render, file_name=file_name,
                      width=width, height=height, title=title, keep_ui_state=keep_ui_state)
        chart.set_data_df(self.result_df)
        chart.draw()

    def fill_gap(self):
        if self.keep_all_timestamp:
            idx = pd.date_range(self.start_timestamp, self.end_timestamp)
            new_index = pd.MultiIndex.from_product([self.result_df.index.levels[0], idx],
                                                   names=['security_id', 'timestamp'])
            self.result_df = self.result_df.loc[~self.result_df.index.duplicated(keep='first')]
            self.result_df = self.result_df.reindex(new_index)
            self.result_df = self.result_df.fillna(method=self.fill_method, limit=self.effective_number)

    def on_data_loaded(self, data: pd.DataFrame):
        self.compute()

    def on_data_changed(self, data: pd.DataFrame):
        """
        overwrite it for computing fast

        Parameters
        ----------
        data :
        """
        self.compute()

    def on_category_data_added(self, category, added_data: pd.DataFrame):
        """
        overwrite it for computing fast

        Parameters
        ----------
        category :
        added_data :
        """
        self.compute()


class FilterFactor(Factor):
    factor_type = FactorType.filter


class ScoreFactor(Factor):
    factor_type = FactorType.score

    def __init__(self, data_schema: object,
                 security_list: List[str] = None,
                 security_type: Union[str, SecurityType] = SecurityType.stock,
                 exchanges: List[str] = ['sh', 'sz'],
                 codes: List[str] = None,
                 the_timestamp: Union[str, pd.Timestamp] = None,
                 start_timestamp: Union[str, pd.Timestamp] = None,
                 end_timestamp: Union[str, pd.Timestamp] = None,
                 columns: List = None, filters: List = None,
                 provider: Union[str, Provider] = 'eastmoney',
                 level: TradingLevel = TradingLevel.LEVEL_1DAY,
                 real_time: bool = False, refresh_interval: int = 10,
                 category_field: str = 'security_id',
                 keep_all_timestamp: bool = False,
                 fill_method: str = 'ffill',
                 effective_number: int = 10,
                 # child added arguments
                 depth_computing_method='ma',
                 depth_computing_param={'window': '100D', 'on': 'timestamp'},
                 breadth_computing_method='quantile',
                 breadth_computing_param={'score_levels': [0.1, 0.3, 0.5, 0.7, 0.9]}) -> None:
        self.depth_computing_method = depth_computing_method
        self.depth_computing_param = depth_computing_param

        self.breadth_computing_method = breadth_computing_method
        self.breadth_computing_param = breadth_computing_param

        super().__init__(data_schema, security_list, security_type, exchanges, codes, the_timestamp, start_timestamp,
                         end_timestamp, columns, filters, provider, level, real_time, refresh_interval, category_field,
                         keep_all_timestamp, fill_method, effective_number)

    def depth_computing(self):
        self.depth_df = self.data_df.reset_index(level='timestamp')

        if self.depth_computing_method == 'ma':
            window = self.depth_computing_param['window']

            on = self.depth_computing_param['on']

            if on == 'timestamp':
                if isinstance(window, pd.DateOffset):
                    window = '{}D'.format(self.window.days)

                self.depth_df = self.depth_df.groupby(level=0).rolling(window=window,
                                                                       on='timestamp').mean()
            else:
                assert type(window) == int
                self.depth_df = self.depth_df.groupby(level=0).rolling(window=window).mean()
        elif self.depth_computing_method == 'count':
            window = self.depth_computing_param['window']
            if isinstance(window, pd.DateOffset):
                window = '{}D'.format(self.window.days)

            self.depth_df = self.depth_df.groupby(level=0).rolling(window=window, on='timestamp').count()

        self.depth_df = self.depth_df.reset_index(level=0, drop=True)
        self.depth_df = self.depth_df.set_index('timestamp', append=True)

        self.depth_df = self.depth_df.loc[(slice(None), slice(self.start_timestamp, self.end_timestamp)), :]

        self.logger.info('factor:{},depth_df:\n{}'.format(self.factor_name, self.depth_df))

    def breadth_computing(self):
        if self.breadth_computing_method == 'quantile':
            self.score_levels = self.breadth_computing_param['score_levels']
            self.score_levels.sort(reverse=True)

            self.quantile = self.depth_df.groupby(level=1).quantile(self.score_levels)
            self.quantile.index.names = ['timestamp', 'score']

            self.logger.info('factor:{},quantile:\n{}'.format(self.factor_name, self.quantile))

            self.result_df = self.depth_df.copy()
            self.result_df.reset_index(inplace=True, level='security_id')
            self.result_df['quantile'] = None
            for timestamp in self.quantile.index.levels[0]:
                length = len(self.result_df.loc[self.result_df.index == timestamp, 'quantile'])
                self.result_df.loc[self.result_df.index == timestamp, 'quantile'] = [self.quantile.loc[
                                                                                         timestamp].to_dict()] * length

            self.logger.info('factor:{},df with quantile:\n{}'.format(self.factor_name, self.result_df))

            # self.result_df = self.result_df.set_index(['security_id'], append=True)
            # self.result_df = self.result_df.sort_index(level=[0, 1])
            #
            # self.logger.info(self.result_df)
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
                self.result_df[factor] = self.result_df.apply(lambda x: calculate_score(x, factor, x['quantile']),
                                                              axis=1)

            self.result_df = self.result_df.reset_index()
            self.result_df = index_df_with_security_time(self.result_df)
            self.result_df = self.result_df.loc[:, self.factors]

            self.result_df = self.result_df.loc[~self.result_df.index.duplicated(keep='first')]

            self.logger.info('factor:{},df:\n{}'.format(self.factor_name, self.result_df))

            self.fill_gap()


class StateFactor(Factor):
    factor_type = FactorType.state
    states = []

    def get_state(self, timestamp, security_id):
        pass

    def get_short_state(self):
        pass

    def get_long_state(self):
        pass
