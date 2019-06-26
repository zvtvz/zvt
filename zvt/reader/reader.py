# -*- coding: utf-8 -*-
import logging
import time
from typing import List, Union

import pandas as pd
import plotly.graph_objs as go

from zvt.api.common import get_data, Stock1DKdata, get_exchange
from zvt.charts import Chart
from zvt.domain import SecurityType, TradingLevel, Provider
from zvt.utils.pd_utils import index_df_with_category_time, df_is_not_null
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
                 security_list: List[str] = None,
                 security_type: Union[str, SecurityType] = SecurityType.stock,
                 exchanges: List[str] = ['sh', 'sz'],
                 codes: List[str] = None,
                 the_timestamp: Union[str, pd.Timestamp] = None,
                 start_timestamp: Union[str, pd.Timestamp] = '2018-01-01',
                 end_timestamp: Union[str, pd.Timestamp] = '2019-06-23',
                 columns: List = None,
                 filters: List = None,
                 provider: Union[str, Provider] = 'eastmoney',
                 level: TradingLevel = TradingLevel.LEVEL_1DAY,
                 real_time: bool = False,
                 refresh_interval: int = 10,
                 category_field: str = 'security_id') -> None:
        """

        Parameters
        ----------
        data_schema :
        security_list : use security_list if possible
        security_type :
        exchanges :
        codes : security_type + exchanges + codes make security_list
        the_timestamp : if set,just read the data in specific time
        start_timestamp :
        end_timestamp :
        columns : the columns in data_schema for reading
        filters : sqlalchemy filters
        provider :
        level :
        real_time : data is history + happening event,real_time means reading the happening data if possible
        refresh_interval :
        category_field : the level 0 index for the df
        """
        self.data_schema = data_schema

        if the_timestamp:
            self.start_timestamp = the_timestamp
            self.end_timestamp = the_timestamp
        else:
            self.start_timestamp = start_timestamp
            self.end_timestamp = end_timestamp

        self.start_timestamp = to_pd_timestamp(self.start_timestamp)
        self.end_timestamp = to_pd_timestamp(self.end_timestamp)

        self.security_type = security_type
        self.exchanges = exchanges
        self.codes = codes
        self.security_list = security_list

        if not self.security_list:
            # if not (self.security_type and self.exchanges):
            #     raise Exception(
            #         'you should set (security_type,exchanges) or (security_type,exchanges) or (security_list) for the reader')

            self.security_list = []
            if self.security_type and self.exchanges and self.codes:
                # for china stock,just need codes
                if self.security_type == SecurityType.stock:
                    for code in self.codes:
                        self.security_list.append('{}_{}_{}'.format(self.security_type.value, get_exchange(code), code))
                else:
                    for exchange in self.exchanges:
                        for code in self.codes:
                            self.security_list.append('{}_{}_{}'.format(self.security_type.value, exchange, code))

        self.provider = provider
        self.level = level
        self.filters = filters
        self.real_time = real_time
        self.refresh_interval = refresh_interval
        self.category_field = category_field

        self.category_column = eval('self.data_schema.{}'.format(self.category_field))
        self.columns = columns

        # we store the data in a multiple index(category_column,timestamp) Dataframe
        if self.columns:
            self.columns = set(columns) | {self.category_column, self.data_schema.timestamp}

        self.data_listeners: List[DataListener] = []

        self.data_df: pd.DataFrame = None

        self.load_data()

    def load_data(self):
        if self.security_list:
            self.data_df = get_data(data_schema=self.data_schema, security_list=self.security_list,
                                    provider=self.provider, columns=self.columns,
                                    start_timestamp=self.start_timestamp,
                                    end_timestamp=self.end_timestamp, filters=self.filters, level=self.level)
        else:
            self.data_df = get_data(data_schema=self.data_schema, codes=self.codes,
                                    provider=self.provider, columns=self.columns,
                                    start_timestamp=self.start_timestamp,
                                    end_timestamp=self.end_timestamp, filters=self.filters, level=self.level)

        if df_is_not_null(self.data_df):
            self.data_df = index_df_with_category_time(self.data_df, category=self.category_field)

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
                        added = index_df_with_category_time(would_added, category=self.category_field)
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

        return changed

    def run(self):
        self.load_data()
        if self.real_time:
            while True:
                self.move_on(to_timestamp=now_pd_timestamp())
                time.sleep(self.refresh_interval)

    def register_data_listener(self, listener):
        if listener not in self.data_listeners:
            self.data_listeners.append(listener)

        # notify it once after registered
        if df_is_not_null(self.data_df):
            listener.on_data_loaded(self.data_df)

    def deregister_data_listener(self, listener):
        if listener in self.data_listeners:
            self.data_listeners.remove(listener)

    def draw(self,
             figures=[go.Scatter],
             modes=['lines'],
             value_fields=['close'],
             render='html',
             file_name=None,
             width=None,
             height=None,
             title=None,
             keep_ui_state=True,
             annotation_df=None):
        chart = Chart(category_field=self.category_field, figures=figures, modes=modes, value_fields=value_fields,
                      render=render, file_name=file_name,
                      width=width, height=height, title=title, keep_ui_state=keep_ui_state)
        chart.set_data_df(self.data_df)
        chart.set_annotation_df(annotation_df)
        return chart.draw()


if __name__ == '__main__':
    data_reader = DataReader(codes=['000338', '600651'], data_schema=Stock1DKdata, provider='joinquant',
                             start_timestamp='2008-01-01',
                             end_timestamp='2019-06-30',
                             real_time=True)
    data_reader.draw()
