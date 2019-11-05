# -*- coding: utf-8 -*-
import enum
import logging
import time
from typing import List, Union

import pandas as pd

from zvdata import IntervalLevel
from zvdata.api import get_data, df_to_db
from zvdata.normal_data import NormalData
from zvdata.reader import DataReader, DataListener
from zvdata.utils.pd_utils import pd_is_not_null
from zvt.drawer.drawer import Drawer
from zvt.sedes import Jsonable


class Transformer(object):
    logger = logging.getLogger(__name__)

    indicator_cols = []

    def transform(self, input_df) -> pd.DataFrame:
        return input_df


class Accumulator(object):
    logger = logging.getLogger(__name__)

    def acc(self, input_df, acc_df) -> pd.DataFrame:
        return acc_df


class Scorer(object):
    logger = logging.getLogger(__name__)

    def score(self, input_df) -> pd.DataFrame:
        return input_df


class FactorType(enum.Enum):
    filter = 'filter'
    score = 'score'
    state = 'state'


class Factor(DataReader, DataListener, Jsonable):
    factor_type: FactorType = None

    # define the schema for persist
    factor_schema = None

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
                 computing_window: int = 250,
                 # child added arguments
                 keep_all_timestamp: bool = False,
                 fill_method: str = 'ffill',
                 effective_number: int = 10,
                 transformer: Transformer = None,
                 accumulator: Accumulator = None,
                 need_persist: bool = True,
                 dry_run: bool = False) -> None:

        super().__init__(data_schema, entity_ids, entity_type, exchanges, codes, the_timestamp, start_timestamp,
                         end_timestamp, columns, filters, order, limit, provider, level,
                         category_field, time_field, computing_window)

        self.factor_name = type(self).__name__.lower()

        self.keep_all_timestamp = keep_all_timestamp
        self.fill_method = fill_method
        self.effective_number = effective_number
        self.transformer = transformer
        self.accumulator = accumulator

        self.need_persist = need_persist
        self.dry_run = dry_run

        # 计算因子的结果，可持久化
        self.factor_df: pd.DataFrame = None
        # 中间结果，不持久化
        self.pipe_df: pd.DataFrame = None
        # result_df是用于选股的标准df
        self.result_df: pd.DataFrame = None

        # 如果是accumulate类的运算，需要利用之前的factor_df,比如全市场的一些统计信息
        if self.need_persist:
            # 如果只是为了计算因子，只需要读取valid_window的factor_df
            if self.dry_run:
                self.factor_df = self.load_window_df(provider='zvt', data_schema=self.factor_schema)
            else:
                self.factor_df = get_data(provider='zvt',
                                          data_schema=self.factor_schema,
                                          start_timestamp=self.start_timestamp,
                                          index=[self.category_field, self.time_field])

        if pd_is_not_null(self.factor_df):
            dfs = []
            for entity_id, df in self.data_df.groupby(level=0):
                if entity_id in self.factor_df.index.levels[0]:
                    df = df[df.timestamp >= self.factor_df.loc[(entity_id,)].index[0]]
                dfs.append(df)

            self.data_df = pd.concat(dfs)

        self.register_data_listener(self)

    def pre_compute(self):
        if not pd_is_not_null(self.pipe_df):
            self.pipe_df = self.data_df

    def do_compute(self):
        # 无状态的转换运算
        if pd_is_not_null(self.data_df) and self.transformer:
            self.pipe_df = self.transformer.transform(self.data_df)

        # 有状态的累加运算
        if pd_is_not_null(self.pipe_df) and self.accumulator:
            self.factor_df = self.accumulator.acc(self.pipe_df, self.factor_df)
        else:
            self.factor_df = self.pipe_df

    def after_compute(self):
        self.fill_gap()

        if self.need_persist:
            self.persist_result()

    def compute(self):
        """
        implement this to calculate factors normalize to [0,1]

        """
        self.pre_compute()

        self.logger.info('do_compute start')
        start_time = time.time()
        self.do_compute()
        cost_time = time.time() - start_time
        self.logger.info('do_compute finish,cost_time:{}'.format(cost_time))

        self.logger.info('after_compute start')
        start_time = time.time()
        self.after_compute()
        cost_time = time.time() - start_time
        self.logger.info('after_compute finish,cost_time:{}'.format(cost_time))

    def __repr__(self) -> str:
        return self.result_df.__repr__()

    def get_result_df(self):
        return self.result_df

    def get_pipe_df(self):
        return self.pipe_df

    def get_factor_df(self):
        return self.factor_df

    def pipe_drawer(self) -> Drawer:
        drawer = Drawer(NormalData(df=self.pipe_df))
        return drawer

    def result_drawer(self) -> Drawer:
        return Drawer(NormalData(df=self.result_df))

    def draw_pipe(self, chart='line', plotly_layout=None, annotation_df=None, render='html', file_name=None,
                  width=None, height=None,
                  title=None, keep_ui_state=True, **kwargs):
        return self.pipe_drawer().draw(chart=chart, plotly_layout=plotly_layout, annotation_df=annotation_df,
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
        overwrite it for computing after data added

        Parameters
        ----------
        data :
        """
        self.compute()

    def on_entity_data_changed(self, entity, added_data: pd.DataFrame):
        """
        overwrite it for computing after entity data added

        Parameters
        ----------
        entity :
        added_data :
        """
        pass

    def persist_result(self):
        df_to_db(df=self.factor_df, data_schema=self.factor_schema, provider='zvt')

    def get_latest_saved_pipe(self):
        order = eval('self.factor_schema.{}.desc()'.format(self.time_field))

        records = get_data(provider=self.provider,
                           data_schema=self.pipe_schema,
                           order=order,
                           limit=1,
                           return_type='domain',
                           session=self.session)
        if records:
            return records[0]
        return None


class FilterFactor(Factor):
    factor_type = FactorType.filter


class ScoreFactor(Factor):
    factor_type = FactorType.score

    def __init__(self, data_schema: object, entity_ids: List[str] = None, entity_type: str = 'stock',
                 exchanges: List[str] = ['sh', 'sz'], codes: List[str] = None,
                 the_timestamp: Union[str, pd.Timestamp] = None, start_timestamp: Union[str, pd.Timestamp] = None,
                 end_timestamp: Union[str, pd.Timestamp] = None, columns: List = None, filters: List = None,
                 order: object = None, limit: int = None, provider: str = 'eastmoney',
                 level: Union[str, IntervalLevel] = IntervalLevel.LEVEL_1DAY, category_field: str = 'entity_id',
                 time_field: str = 'timestamp', keep_all_timestamp: bool = False,
                 fill_method: str = 'ffill', effective_number: int = 10, transformer: Transformer = None,
                 need_persist: bool = True,
                 dry_run: bool = True,
                 scorer: Scorer = None) -> None:
        self.scorer = scorer
        super().__init__(data_schema, entity_ids, entity_type, exchanges, codes, the_timestamp, start_timestamp,
                         end_timestamp, columns, filters, order, limit, provider, level, category_field, time_field,
                         keep_all_timestamp, fill_method, effective_number, transformer, need_persist,
                         dry_run)

    def do_compute(self):
        super().do_compute()

        if pd_is_not_null(self.pipe_df) and self.scorer:
            self.result_df = self.scorer.score(self.data_df)


class StateFactor(Factor):
    factor_type = FactorType.state
    states = []

    def get_state(self, timestamp, entity_id):
        pass

    def get_short_state(self):
        pass

    def get_long_state(self):
        pass
