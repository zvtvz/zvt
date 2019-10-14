# -*- coding: utf-8 -*-
import json
import logging
import time
from typing import List, Union

import pandas as pd

from zvdata import IntervalLevel
from zvdata.api import get_data
from zvdata.chart import Drawer
from zvdata.normal_data import NormalData
from zvdata.utils.pd_utils import df_is_not_null
from zvdata.utils.time_utils import to_pd_timestamp, now_pd_timestamp
from zvt.domain import Stock1dKdata


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


class DataReader(object):
    logger = logging.getLogger(__name__)

    def __init__(self,
                 data_schema: object,
                 entity_ids: List[str] = None,
                 entity_type: str = 'stock',
                 exchanges: List[str] = ['sh', 'sz'],
                 codes: List[str] = None,
                 the_timestamp: Union[str, pd.Timestamp] = None,
                 start_timestamp: Union[str, pd.Timestamp] = '2018-01-01',
                 end_timestamp: Union[str, pd.Timestamp] = now_pd_timestamp(),
                 columns: List = None,
                 filters: List = None,
                 order: object = None,
                 limit: int = None,
                 provider: str = 'joinquant',
                 level: IntervalLevel = IntervalLevel.LEVEL_1DAY,
                 category_field: str = 'entity_id',
                 time_field: str = 'timestamp',
                 auto_load: bool = True,
                 valid_window: int = 250) -> None:
        self.data_schema = data_schema

        self.the_timestamp = the_timestamp
        if the_timestamp:
            self.start_timestamp = the_timestamp
            self.end_timestamp = the_timestamp
        else:
            self.start_timestamp = start_timestamp
            self.end_timestamp = end_timestamp

        self.start_timestamp = to_pd_timestamp(self.start_timestamp)
        self.end_timestamp = to_pd_timestamp(self.end_timestamp)

        self.entity_type = entity_type
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

        self.provider = provider
        self.filters = filters
        self.order = order
        self.limit = limit

        if level:
            self.level = IntervalLevel(level)
        else:
            self.level = level

        self.category_field = category_field
        self.time_field = time_field
        self.auto_load = auto_load
        self.valid_window = valid_window

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

        if self.auto_load:
            self.load_data()

    def load_data(self):
        if self.entity_ids:
            self.data_df = get_data(data_schema=self.data_schema, entity_ids=self.entity_ids,
                                    provider=self.provider, columns=self.columns,
                                    start_timestamp=self.start_timestamp,
                                    end_timestamp=self.end_timestamp, filters=self.filters, order=self.order,
                                    limit=self.limit,
                                    level=self.level,
                                    index=[self.category_field, self.time_field],
                                    time_field=self.time_field)
        else:
            self.data_df = get_data(data_schema=self.data_schema, codes=self.codes,
                                    provider=self.provider, columns=self.columns,
                                    start_timestamp=self.start_timestamp,
                                    end_timestamp=self.end_timestamp, filters=self.filters, order=self.order,
                                    limit=self.limit,
                                    level=self.level,
                                    index=[self.category_field, self.time_field],
                                    time_field=self.time_field)

        for listener in self.data_listeners:
            listener.on_data_loaded(self.data_df)

    def move_on(self, to_timestamp: Union[str, pd.Timestamp] = None,
                timeout: int = 20) -> object:
        """
        1)get the data happened before to_timestamp,if not set,get all the data which means to now
        2)remove the data outside valid_window for saving memory,after move_on you should know that the data_df has changed


        :param to_timestamp:
        :type to_timestamp:
        :param timeout:
        :type timeout: int
        :return:
        :rtype:
        """
        if not df_is_not_null(self.data_df):
            self.load_data()
            return

        start_time = time.time()

        # FIXME:we suppose history data should be there at first
        has_got = []
        dfs = []
        for entity_id, df in self.data_df.groupby(level=0):
            if entity_id in has_got:
                continue
            if len(has_got) == len(self.data_df.index.levels[0]):
                break

            recorded_timestamp = df['timestamp'].max()
            df = df.iloc[-self.valid_window:]

            added_filter = [self.category_col == entity_id, self.time_col > recorded_timestamp]
            if self.filters:
                filters = self.filters + added_filter
            else:
                filters = added_filter

            added_df = get_data(data_schema=self.data_schema, provider=self.provider, columns=self.columns,
                                end_timestamp=to_timestamp, filters=filters, level=self.level,
                                index=[self.category_field, self.time_field])

            if df_is_not_null(added_df):
                self.logger.info('entity_id:{},added:\n{}'.format(entity_id, added_df))

                for listener in self.data_listeners:
                    listener.on_entity_data_changed(entity=entity_id, added_data=added_df)
                # if got data,just move to another entity_id
                has_got.append(entity_id)
                df = df.append(added_df)

            dfs.append(df)

            cost_time = time.time() - start_time
            if cost_time > timeout:
                self.logger.warning(
                    'category:{} level:{} getting data timeout,to_timestamp:{},now:{}'.format(entity_id, self.level,
                                                                                              to_timestamp,
                                                                                              now_pd_timestamp()))
                break

        if dfs:
            self.data_df = pd.concat(dfs)
            self.data_df.sort_index(level=[0, 1])

            for listener in self.data_listeners:
                listener.on_data_changed(self.data_df)

    def register_data_listener(self, listener):
        if listener not in self.data_listeners:
            self.data_listeners.append(listener)

        # notify it once after registered
        if df_is_not_null(self.data_df):
            listener.on_data_loaded(self.data_df)

    def deregister_data_listener(self, listener):
        if listener in self.data_listeners:
            self.data_listeners.remove(listener)

    def data_drawer(self) -> Drawer:
        return Drawer(data=NormalData(df=self.data_df))

    def empty(self):
        return not df_is_not_null(self.data_df)


if __name__ == '__main__':
    data_reader = DataReader(codes=['002572', '000338'], data_schema=Stock1dKdata, provider='joinquant',
                             start_timestamp='2017-01-01',
                             end_timestamp='2019-06-10')

    for timestamp in pd.date_range(start='2019-06-10', end='2019-10-10'):
        data_reader.move_on(timestamp)
        print(data_reader.data_df.iloc[0])
