# -*- coding: utf-8 -*-
import enum
from typing import List, Union

import pandas as pd

from zvdata import IntervalLevel
from zvdata.chart import Drawer
from zvdata.domain import get_db_session, FactorDomain
from zvdata.normal_data import NormalData
from zvdata.reader import DataReader, DataListener
from zvdata.score_algorithm import Scorer
from zvdata.sedes import Jsonable, UiComposable


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

    def pre_compute(self):
        self.depth_df = self.data_df

    def do_compute(self):
        pass

    def after_compute(self):
        pass

    def compute(self):
        """
        implement this to calculate factors normalize to [0,1]

        """
        self.pre_compute()
        self.do_compute()
        self.after_compute()

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

    def draw_depth(self, chart='line', plotly_layout=None, annotation_df=None, render='html', file_name=None,
                   width=None, height=None,
                   title=None, keep_ui_state=True, **kwargs):
        return self.depth_drawer().draw(chart=chart, plotly_layout=plotly_layout, annotation_df=annotation_df,
                                        render=render, file_name=file_name,
                                        width=width, height=height, title=title, keep_ui_state=keep_ui_state, **kwargs)

    def draw_result(self, chart='line', plotly_layout=None, annotation_df=None, render='html', file_name=None,
                    width=None, height=None,
                    title=None, keep_ui_state=True, **kwargs):
        return self.result_drawer().draw(chart=chart, plotly_layout=plotly_layout, annotation_df=annotation_df,
                                         render=render, file_name=file_name,
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
                 scorer: Scorer = Scorer()) -> None:
        self.scorer = scorer

        super().__init__(data_schema, entity_ids, entity_type, exchanges, codes, the_timestamp, start_timestamp,
                         end_timestamp, columns, filters, order, limit, provider, level,
                         category_field, time_field, trip_timestamp, auto_load, keep_all_timestamp, fill_method,
                         effective_number)

    def do_compute(self):
        self.result_df = self.scorer.compute(input_df=self.depth_df)

    def after_compute(self):
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
