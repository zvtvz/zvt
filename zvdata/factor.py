# -*- coding: utf-8 -*-
import enum
from typing import List, Union

import pandas as pd

from zvdata.chart import Drawer
from zvdata.domain import get_db_session, FactorDomain
from zvdata.normal_data import NormalData
from zvdata.reader import DataReader, DataListener
from zvdata.sedes import Jsonable, UiComposable
from zvdata.structs import IntervalLevel
from zvdata.utils.pd_utils import index_df_with_category_xfield


class FactorType(enum.Enum):
    filter = 'filter'
    score = 'score'
    state = 'state'


# factor class registry
factor_cls_registry = {}

# factor instance registry
factor_instance_registry = {}


def register_instance(cls, instance):
    if cls.__name__ not in ('Factor', 'FilterFactor', 'ScoreFactor', 'StateFactor'):
        factor_instance_registry[cls.__name__] = instance


def register_class(target_class):
    if target_class.__name__ not in ('Factor', 'FilterFactor', 'ScoreFactor', 'StateFactor'):
        factor_cls_registry[target_class.__name__] = target_class


class Meta(type):
    def __new__(meta, name, bases, class_dict):
        cls = type.__new__(meta, name, bases, class_dict)
        register_class(cls)
        return cls


class Factor(DataReader, DataListener, Jsonable, UiComposable, metaclass=Meta):
    factor_type: FactorType = None

    def __init__(self,
                 data_schema: object,
                 entity_ids: List[str] = None,
                 entity_type: str = 'stock',
                 exchanges: List[str] = ['sh', 'sz'],
                 codes: List[str] = None,
                 the_timestamp: Union[str, pd.Timestamp] = None,
                 start_timestamp: Union[str, pd.Timestamp] = None,
                 end_timestamp: Union[str, pd.Timestamp] = None,
                 columns: List = None,
                 filters: List = None,
                 order: object = None,
                 limit: int = None,
                 provider: str = 'eastmoney',
                 level: Union[str, IntervalLevel] = IntervalLevel.LEVEL_1DAY,

                 category_field: str = 'entity_id',
                 time_field: str = 'timestamp',
                 trip_timestamp: bool = True,
                 auto_load: bool = True,
                 # child added arguments
                 keep_all_timestamp: bool = False,
                 fill_method: str = 'ffill',
                 effective_number: int = 10) -> None:
        if columns:
            self.factors = [item.key for item in columns]

        super().__init__(data_schema, entity_ids, entity_type, exchanges, codes, the_timestamp, start_timestamp,
                         end_timestamp, columns, filters, order, limit, provider, level,
                         category_field, time_field, trip_timestamp, auto_load)

        register_instance(self.__class__, self)

        # using to do db operations
        self.session = get_db_session(provider='zvdata',
                                      data_schema=FactorDomain)

        self.factor_name = type(self).__name__.lower()

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

    def depth_drawer(self) -> Drawer:
        drawer = Drawer(NormalData(df=self.depth_df, index_field=self.time_field, is_timeseries=True))
        return drawer

    def result_drawer(self) -> Drawer:
        return Drawer(NormalData(df=self.result_df, index_field=self.time_field, is_timeseries=True))

    def draw_depth(self, chart='line', plotly_layout=None, annotation_df=None,render='html', file_name=None, width=None, height=None,
                   title=None, keep_ui_state=True, **kwargs):
        return self.depth_drawer().draw(chart=chart, plotly_layout=plotly_layout, annotation_df=annotation_df,render=render, file_name=file_name,
                                        width=width, height=height, title=title, keep_ui_state=keep_ui_state, **kwargs)

    def draw_result(self, chart='line', plotly_layout=None, annotation_df=None,render='html', file_name=None, width=None, height=None,
                    title=None, keep_ui_state=True, **kwargs):
        return self.result_drawer().draw(chart=chart, plotly_layout=plotly_layout, annotation_df=annotation_df,render=render, file_name=file_name,
                                         width=width, height=height, title=title, keep_ui_state=keep_ui_state, **kwargs)

    def fill_gap(self):
        if self.keep_all_timestamp:
            idx = pd.date_range(self.start_timestamp, self.end_timestamp)
            new_index = pd.MultiIndex.from_product([self.result_df.index.levels[0], idx],
                                                   names=['entity_id', self.time_field])
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

    # TODO:
    def persist(self):
        pass

    def load(self):
        pass


class FilterFactor(Factor):
    factor_type = FactorType.filter


class ScoreFactor(Factor):
    factor_type = FactorType.score

    def __init__(self,
                 data_schema: object,
                 entity_ids: List[str] = None,
                 entity_type: str = 'stock',
                 exchanges: List[str] = ['sh', 'sz'],
                 codes: List[str] = None,
                 the_timestamp: Union[str, pd.Timestamp] = None,
                 start_timestamp: Union[str, pd.Timestamp] = None,
                 end_timestamp: Union[str, pd.Timestamp] = None,
                 columns: List = None,
                 filters: List = None,
                 order: object = None,
                 limit: int = None, provider: str = 'eastmoney',
                 level: Union[str, IntervalLevel] = IntervalLevel.LEVEL_1DAY,

                 category_field: str = 'entity_id',
                 time_field: str = 'timestamp',
                 trip_timestamp: bool = True,
                 auto_load: bool = True,
                 keep_all_timestamp: bool = False,
                 fill_method: str = 'ffill',
                 effective_number: int = 10,
                 # child added arguments
                 depth_computing_method='ma',
                 depth_computing_param={'window': '100D', 'on': 'timestamp'},
                 breadth_computing_method='quantile',
                 breadth_computing_param={'score_levels': [0.1, 0.3, 0.5, 0.7, 0.9]}
                 ) -> None:
        self.depth_computing_method = depth_computing_method
        self.depth_computing_param = depth_computing_param

        self.breadth_computing_method = breadth_computing_method
        self.breadth_computing_param = breadth_computing_param

        super().__init__(data_schema, entity_ids, entity_type, exchanges, codes, the_timestamp, start_timestamp,
                         end_timestamp, columns, filters, order, limit, provider, level,
                         category_field, time_field, trip_timestamp, auto_load, keep_all_timestamp, fill_method,
                         effective_number)

    def depth_computing(self):
        if self.depth_computing_method != None:
            self.depth_df = self.data_df.reset_index(level=self.time_field)

            if self.depth_computing_method == 'ma':
                window = self.depth_computing_param['window']

                on = self.depth_computing_param['on']

                if on == self.time_field:
                    if isinstance(window, pd.DateOffset):
                        window = '{}D'.format(self.window.days)

                    self.depth_df = self.depth_df.groupby(level=0).rolling(window=window,
                                                                           on=self.time_field).mean()
                else:
                    assert type(window) == int
                    self.depth_df = self.depth_df.groupby(level=0).rolling(window=window).mean()
            elif self.depth_computing_method == 'count':
                window = self.depth_computing_param['window']
                if isinstance(window, pd.DateOffset):
                    window = '{}D'.format(self.window.days)

                self.depth_df = self.depth_df.groupby(level=0).rolling(window=window, on=self.time_field).count()

            self.depth_df = self.depth_df.reset_index(level=0, drop=True)
            self.depth_df = self.depth_df.set_index(self.time_field, append=True)

            self.depth_df = self.depth_df.loc[(slice(None), slice(self.start_timestamp, self.end_timestamp)), :]

            self.logger.info('factor:{},depth_df:\n{}'.format(self.factor_name, self.depth_df))
        else:
            self.depth_df = self.data_df

    def breadth_computing(self):
        if self.breadth_computing_method == 'quantile':
            self.score_levels = self.breadth_computing_param['score_levels']
            self.score_levels.sort(reverse=True)

            self.quantile = self.depth_df.groupby(level=1).quantile(self.score_levels)
            self.quantile.index.names = [self.time_field, 'score']

            self.logger.info('factor:{},quantile:\n{}'.format(self.factor_name, self.quantile))

            self.result_df = self.depth_df.copy()
            self.result_df.reset_index(inplace=True, level='entity_id')
            self.result_df['quantile'] = None
            for timestamp in self.quantile.index.levels[0]:
                length = len(self.result_df.loc[self.result_df.index == timestamp, 'quantile'])
                self.result_df.loc[self.result_df.index == timestamp, 'quantile'] = [self.quantile.loc[
                                                                                         timestamp].to_dict()] * length

            self.logger.info('factor:{},df with quantile:\n{}'.format(self.factor_name, self.result_df))

            # self.result_df = self.result_df.set_index(['entity_id'], append=True)
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
            self.result_df = index_df_with_category_xfield(self.result_df, category_field=self.category_field,
                                                           xfield=self.time_field)
            self.result_df = self.result_df.loc[:, self.factors]

            self.result_df = self.result_df.loc[~self.result_df.index.duplicated(keep='first')]

            self.logger.info('factor:{},df:\n{}'.format(self.factor_name, self.result_df))

            self.fill_gap()


class StateFactor(Factor):
    factor_type = FactorType.state
    states = []

    def get_state(self, timestamp, entity_id):
        pass

    def get_short_state(self):
        pass

    def get_long_state(self):
        pass
