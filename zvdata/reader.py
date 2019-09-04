# -*- coding: utf-8 -*-
import json
import logging
import time
from typing import List, Union

import pandas as pd

from zvdata.api import get_data
from zvdata.chart import Drawer
from zvdata.normal_data import NormalData
from zvdata import IntervalLevel
from zvdata.utils.pd_utils import index_df_with_category_xfield, df_is_not_null
from zvdata.utils.time_utils import to_pd_timestamp, to_time_str, now_pd_timestamp


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
        data : the data after changed
        """
        raise NotImplementedError

    def on_category_data_added(self, category: str, added_data: pd.DataFrame) -> object:
        """

        Parameters
        ----------
        category : the data category
        added_data : the data added
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
                 end_timestamp: Union[str, pd.Timestamp] = '2019-06-23',
                 columns: List = None,
                 filters: List = None,
                 order: object = None,
                 limit: int = None,
                 provider: str = 'eastmoney',
                 level: IntervalLevel = IntervalLevel.LEVEL_1DAY,
                 category_field: str = 'entity_id',
                 time_field: str = 'timestamp',
                 trip_timestamp: bool = True,
                 auto_load: bool = True) -> None:
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
        self.trip_timestamp = trip_timestamp
        self.auto_load = auto_load

        self.category_column = eval('self.data_schema.{}'.format(self.category_field))
        self.columns = columns

        # we store the data in a multiple index(category_column,timestamp) Dataframe
        if self.columns:
            # support str
            if type(columns[0]) == str:
                self.columns = []
                for col in columns:
                    self.columns.append(eval('data_schema.{}'.format(col)))

            time_col = eval('self.data_schema.{}'.format(self.time_field))

            # always add category_column and time_field for normalizing
            self.columns = list(set(self.columns) | {self.category_column, time_col})

        self.data_listeners: List[DataListener] = []

        self.data_df: pd.DataFrame = None
        self.normal_data: NormalData = None

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
                                    time_field=self.time_field,
                                    index=self.time_field)
        else:
            self.data_df = get_data(data_schema=self.data_schema, codes=self.codes,
                                    provider=self.provider, columns=self.columns,
                                    start_timestamp=self.start_timestamp,
                                    end_timestamp=self.end_timestamp, filters=self.filters, order=self.order,
                                    limit=self.limit,
                                    level=self.level,
                                    time_field=self.time_field,
                                    index=self.time_field)

        if self.trip_timestamp:
            if self.level == IntervalLevel.LEVEL_1DAY:
                self.data_df[self.time_field] = self.data_df[self.time_field].apply(
                    lambda x: to_pd_timestamp(to_time_str(x)))

        if df_is_not_null(self.data_df):
            self.normal_data = NormalData(df=self.data_df, category_field=self.category_field,
                                          index_field=self.time_field, is_timeseries=True)
            self.data_df = self.normal_data.data_df

        for listener in self.data_listeners:
            listener.on_data_loaded(self.data_df)

    def get_data_df(self):
        return self.data_df

    def get_categories(self):
        return list(self.data_df.groupby(level=0).groups.keys())

    def move_on(self, to_timestamp: Union[str, pd.Timestamp] = None,
                timeout: int = 20) -> bool:
        """
        get the data happened before to_timestamp,if not set,get all the data which means to now

        Parameters
        ----------
        to_timestamp :
        timeout : the time waiting the data ready in seconds

        Returns
        -------
        whether got data
        """
        if not df_is_not_null(self.data_df):
            self.load_data()
            return False

        df = self.data_df.reset_index(level='timestamp')
        recorded_timestamps = df.groupby(level=0)['timestamp'].max()

        self.logger.info('level:{},current_timestamps:\n{}'.format(self.level, recorded_timestamps))

        changed = False
        # FIXME:we suppose history data should be there at first
        start_time = time.time()
        for category, recorded_timestamp in recorded_timestamps.iteritems():
            while True:
                category_filter = [self.category_column == category]
                if self.filters:
                    filters = self.filters + category_filter
                else:
                    filters = category_filter

                added = get_data(data_schema=self.data_schema, provider=self.provider, columns=self.columns,
                                 start_timestamp=recorded_timestamp,
                                 end_timestamp=to_timestamp, filters=filters, level=self.level)

                if df_is_not_null(added):
                    would_added = added[added['timestamp'] != recorded_timestamp].copy()
                    if not would_added.empty:
                        added = index_df_with_category_xfield(would_added, category_field=self.category_field,
                                                              xfield=self.time_field)
                        self.logger.info('category:{},added:\n{}'.format(category, added))

                        self.data_df = self.data_df.append(added)
                        self.data_df = self.data_df.sort_index(level=[0, 1])

                        for listener in self.data_listeners:
                            listener.on_category_data_added(category=category, added_data=added)
                        changed = True
                        # if got data,just move to another category
                        break

                cost_time = time.time() - start_time
                if cost_time > timeout:
                    self.logger.warning(
                        'category:{} level:{} getting data timeout,to_timestamp:{},now:{}'.format(category, self.level,
                                                                                                  to_timestamp,
                                                                                                  now_pd_timestamp()))
                    break

        if changed:
            for listener in self.data_listeners:
                listener.on_data_changed(self.data_df)

            # update the normal_data too
            self.normal_data = NormalData(df=self.data_df, category_field=self.category_field,
                                          index_field=self.time_field, is_timeseries=True)

        return changed

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
        return Drawer(data=self.normal_data)

    def is_empty(self):
        return not df_is_not_null(self.data_df)


class MultipleSchemaReader(object):
    pass
