# -*- coding: utf-8 -*-
import json
import logging
import time
from typing import List, Union, Type, Optional

import pandas as pd

from zvt.contract import IntervalLevel, Mixin, EntityMixin
from zvt.contract.api import get_entities
from zvt.contract.drawer import Drawable
from zvt.utils.pd_utils import pd_is_not_null
from zvt.utils.time_utils import to_pd_timestamp, now_pd_timestamp


class DataListener(object):
    def on_data_loaded(self, data: pd.DataFrame) -> object:
        """

        Parameters
        ----------
        data : the data loaded at first time
        """
        raise NotImplementedError

    def on_data_changed(self, data: pd.DataFrame) -> object:
        """

        Parameters
        ----------
        data : the data added
        """
        raise NotImplementedError

    def on_entity_data_changed(self, entity: str, added_data: pd.DataFrame) -> object:
        """

        Parameters
        ----------
        entity : the entity
        added_data : the data added for the entity
        """
        pass


class DataReader(Drawable):
    logger = logging.getLogger(__name__)

    def __init__(self,
                 data_schema: Type[Mixin],
                 entity_schema: Type[EntityMixin],
                 provider: str = None,
                 entity_provider: str = None,
                 entity_ids: List[str] = None,
                 exchanges: List[str] = None,
                 codes: List[str] = None,
                 the_timestamp: Union[str, pd.Timestamp] = None,
                 start_timestamp: Union[str, pd.Timestamp] = None,
                 end_timestamp: Union[str, pd.Timestamp] = now_pd_timestamp(),
                 columns: List = None,
                 filters: List = None,
                 order: object = None,
                 limit: int = None,
                 level: IntervalLevel = None,
                 category_field: str = 'entity_id',
                 time_field: str = 'timestamp',
                 computing_window: int = None) -> None:
        super().__init__()
        self.logger = logging.getLogger(self.__class__.__name__)

        self.data_schema = data_schema
        self.entity_schema = entity_schema

        self.provider = provider
        self.entity_provider = entity_provider

        self.the_timestamp = the_timestamp
        if the_timestamp:
            self.start_timestamp = the_timestamp
            self.end_timestamp = the_timestamp
        else:
            self.start_timestamp = start_timestamp
            self.end_timestamp = end_timestamp

        self.start_timestamp = to_pd_timestamp(self.start_timestamp)
        self.end_timestamp = to_pd_timestamp(self.end_timestamp)

        self.exchanges = exchanges

        if codes:
            if type(codes) == str:
                codes = codes.replace(' ', '')
                if codes.startswith('[') and codes.endswith(']'):
                    codes = json.loads(codes)
                else:
                    codes = codes.split(',')

        self.codes = codes
        self.entity_ids = entity_ids

        # 转换成标准entity_id
        if entity_schema and not self.entity_ids:
            df = get_entities(entity_schema=entity_schema, provider=self.entity_provider,
                              exchanges=self.exchanges, codes=self.codes)
            if pd_is_not_null(df):
                self.entity_ids = df['entity_id'].to_list()

        self.filters = filters
        self.order = order
        self.limit = limit

        if level:
            self.level = IntervalLevel(level)
        else:
            self.level = level

        self.category_field = category_field
        self.time_field = time_field
        self.computing_window = computing_window

        self.category_col = eval('self.data_schema.{}'.format(self.category_field))
        self.time_col = eval('self.data_schema.{}'.format(self.time_field))

        self.columns = columns

        # we store the data in a multiple index(category_column,timestamp) Dataframe
        if self.columns:
            # support str
            if type(columns[0]) == str:
                self.columns = []
                for col in columns:
                    self.columns.append(eval('data_schema.{}'.format(col)))

            # always add category_column and time_field for normalizing
            self.columns = list(set(self.columns) | {self.category_col, self.time_col})

        self.data_listeners: List[DataListener] = []

        self.data_df: pd.DataFrame = None

        self.load_data()

    def load_window_df(self, provider, data_schema, window):
        window_df = None

        dfs = []
        for entity_id in self.entity_ids:
            df = data_schema.query_data(provider=provider,
                                        index=[self.category_field, self.time_field],
                                        order=data_schema.timestamp.desc(),
                                        entity_id=entity_id,
                                        limit=window)
            if pd_is_not_null(df):
                dfs.append(df)
        if dfs:
            window_df = pd.concat(dfs)
            window_df = window_df.sort_index(level=[0, 1])
        return window_df

    def load_data(self):
        self.logger.info('load_data start')
        start_time = time.time()
        params = dict(entity_ids=self.entity_ids, provider=self.provider,
                      columns=self.columns, start_timestamp=self.start_timestamp,
                      end_timestamp=self.end_timestamp, filters=self.filters,
                      order=self.order, limit=self.limit, level=self.level,
                      index=[self.category_field, self.time_field],
                      time_field=self.time_field)
        self.logger.info(f'query_data params:{params}')

        self.data_df = self.data_schema.query_data(entity_ids=self.entity_ids, provider=self.provider,
                                                   columns=self.columns, start_timestamp=self.start_timestamp,
                                                   end_timestamp=self.end_timestamp, filters=self.filters,
                                                   order=self.order, limit=self.limit, level=self.level,
                                                   index=[self.category_field, self.time_field],
                                                   time_field=self.time_field)

        cost_time = time.time() - start_time
        self.logger.info('load_data finished, cost_time:{}'.format(cost_time))

        for listener in self.data_listeners:
            listener.on_data_loaded(self.data_df)

    def move_on(self, to_timestamp: Union[str, pd.Timestamp] = None,
                timeout: int = 20) -> object:
        """
        using continual fetching data in realtime
        1)get the data happened before to_timestamp,if not set,get all the data which means to now
        2)if computing_window set,the data_df would be cut for saving memory


        :param to_timestamp:
        :type to_timestamp:
        :param timeout:
        :type timeout: int
        :return:
        :rtype:
        """
        if not pd_is_not_null(self.data_df):
            self.load_data()
            return

        start_time = time.time()

        # FIXME:we suppose history data should be there at first
        has_got = []
        dfs = []
        changed = False
        while True:
            for entity_id, df in self.data_df.groupby(level=0):
                if entity_id in has_got:
                    continue

                recorded_timestamp = df.index.levels[1].max()

                # move_on读取数据，表明之前的数据已经处理完毕，只需要保留computing_window的数据
                if self.computing_window:
                    df = df.iloc[-self.computing_window:]

                added_filter = [self.category_col == entity_id, self.time_col > recorded_timestamp]
                if self.filters:
                    filters = self.filters + added_filter
                else:
                    filters = added_filter

                added_df = self.data_schema.query_data(provider=self.provider,
                                                       columns=self.columns,
                                                       end_timestamp=to_timestamp, filters=filters, level=self.level,
                                                       index=[self.category_field, self.time_field])

                if pd_is_not_null(added_df):
                    self.logger.info(f'got new data:{df.to_json(orient="records", force_ascii=False)}')

                    for listener in self.data_listeners:
                        listener.on_entity_data_changed(entity=entity_id, added_data=added_df)
                    # if got data,just move to another entity_id
                    changed = True
                    has_got.append(entity_id)
                    df = df.append(added_df, sort=False)
                    dfs.append(df)
                else:
                    cost_time = time.time() - start_time
                    if cost_time > timeout:
                        # if timeout,just add the old data
                        has_got.append(entity_id)
                        dfs.append(df)
                        self.logger.warning(
                            'category:{} level:{} getting data timeout,to_timestamp:{},now:{}'.format(entity_id,
                                                                                                      self.level,
                                                                                                      to_timestamp,
                                                                                                      now_pd_timestamp()))
                        continue

            if len(has_got) == len(self.data_df.index.levels[0]):
                break

        if dfs:
            self.data_df = pd.concat(dfs, sort=False)
            self.data_df.sort_index(level=[0, 1], inplace=True)

            if changed:
                for listener in self.data_listeners:
                    listener.on_data_changed(self.data_df)

    def register_data_listener(self, listener):
        if listener not in self.data_listeners:
            self.data_listeners.append(listener)

        # notify it once after registered
        if pd_is_not_null(self.data_df):
            listener.on_data_loaded(self.data_df)

    def deregister_data_listener(self, listener):
        if listener in self.data_listeners:
            self.data_listeners.remove(listener)

    def empty(self):
        return not pd_is_not_null(self.data_df)

    def drawer_main_df(self) -> Optional[pd.DataFrame]:
        return self.data_df


__all__ = ['DataListener', 'DataReader']

if __name__ == '__main__':
    from zvt.domain import Stock1dKdata, Stock

    data_reader = DataReader(codes=['002572', '000338'], data_schema=Stock1dKdata, entity_schema=Stock,
                             start_timestamp='2017-01-01',
                             end_timestamp='2019-06-10')

    data_reader.draw(show=True)
