# -*- coding: utf-8 -*-
import enum
import logging
import time

import pandas as pd

from zvt.api.common import get_one_day_trading_minutes, get_close_time, get_data
from zvt.api.technical import get_securities
from zvt.domain import TradingLevel, get_db_session, Provider, SecurityType, get_store_category
from zvt.utils.time_utils import is_same_date, now_pd_timestamp, to_pd_timestamp
from zvt.utils.utils import fill_domain_from_dict


class ApiWrapper(object):
    logger = logging.getLogger(__name__)

    def request(self, url=None, method='post', param=None, path_fields=None):
        raise NotImplementedError


class Recorder(object):
    logger = logging.getLogger(__name__)

    # overwrite them to setup the data you want to record
    provider: Provider = None
    data_schema = None

    url = None

    def __init__(self,
                 batch_size=10,
                 force_update=False,
                 sleeping_time=10) -> None:
        """

        :param batch_size:batch size to saving to db
        :type batch_size:int
        :param force_update: whether force update the data even if it exists
        :type force_update:bool
        :param sleeping_time:sleeping seconds for recoding loop
        :type sleeping_time:int
        """

        assert self.provider is not None
        assert self.data_schema is not None

        self.store_category = get_store_category(data_schema=self.data_schema)

        self.batch_size = batch_size
        self.force_update = force_update
        self.sleeping_time = sleeping_time

        # using to do db operations
        self.session = get_db_session(provider=self.provider,
                                      store_category=self.store_category)

    def run(self):
        raise NotImplementedError

    def sleep(self):
        time.sleep(self.sleeping_time)


class RecorderForSecurities(Recorder):
    # overwrite them to fetch the security list
    meta_provider: Provider = None
    meta_schema = None

    def __init__(self,
                 security_type=SecurityType.stock,
                 exchanges=['sh', 'sz'],
                 codes=None,
                 batch_size=10,
                 force_update=False,
                 sleeping_time=10) -> None:
        super().__init__(batch_size=batch_size, force_update=force_update, sleeping_time=sleeping_time)

        assert self.meta_provider is not None
        assert self.meta_schema is not None
        self.meta_category = get_store_category(data_schema=self.meta_schema)

        # setup the securities you want to record
        self.security_type = security_type
        self.exchanges = exchanges
        self.codes = codes

        self.meta_session = get_db_session(provider=self.meta_provider, store_category=self.meta_category)
        # init the security list
        self.securities = get_securities(session=self.meta_session,
                                         security_type=self.security_type,
                                         exchanges=self.exchanges,
                                         codes=self.codes,
                                         return_type='domain',
                                         provider=self.meta_provider)


class TimeSeriesFetchingStyle(enum.Enum):
    # 按开始时间获取
    start = 'start'
    # 按结束时间获取
    end = 'end'
    # 按时间区间获取
    start_end = 'start_end'
    # 按返回条数获取
    size = 'size'
    # 按开始时间和返回条数获取
    start_size = 'start_size'
    # 按结束时间和返回条数获取
    end_size = 'end_size'
    # 按给定的时间数组获取
    timestamps = 'timestamps'


class TimeSeriesDataRecorder(RecorderForSecurities):
    api_wrapper = None  # type: ApiWrapper
    request_method = 'post'
    # 返回json数据中需要的数据的path组成的列表
    path_fields = None

    def __init__(self, security_type=SecurityType.stock, exchanges=['sh', 'sz'], codes=None, batch_size=10,
                 force_update=False, sleeping_time=5, fetching_style=TimeSeriesFetchingStyle.end_size,
                 default_size=2000, one_shot=False) -> None:
        super().__init__(security_type, exchanges, codes, batch_size, force_update, sleeping_time)

        self.fetching_style = fetching_style
        self.default_size = default_size
        self.one_shot = one_shot

    def evaluate_start_end_size_timestamps(self, security_item):
        """
        evaluate the size for recording data
        :param security_item:
        :type security_item: str
        :return:the start,end,size need to recording,size=0 means finish recording
        :rtype:(pd.Timestamp,pd.Timestamp,int)
        """

        # get latest record
        latest_record = get_data(security_id=security_item.id,
                                 provider=self.provider,
                                 data_schema=self.data_schema,
                                 order=self.data_schema.timestamp.desc(), limit=1,
                                 return_type='domain',
                                 session=self.session)

        if latest_record:
            latest_timestamp = latest_record[0].timestamp
        else:
            latest_timestamp = security_item.timestamp

        if not latest_timestamp:
            return None, None, self.default_size, None

        return latest_timestamp, None, self.default_size, None

    def generate_request_param(self, security_item, start, end, size, timestamp):
        raise NotImplementedError

    def get_data_map(self):
        raise NotImplementedError

    def record(self, security_item, start, end, size, timestamps):
        """
        the method you need to implement to record data,it should return the list of data which could be used to
        generate_domain

        :param security_item:
        :type security_item: Union[Stock]
        :param start:pd.Timestamp
        :type start:
        :param end:pd.Timestamp
        :type end:
        :param size:
        :type size:int
        :param timestamps:timestamp list to record
        :type timestamps:list of pd.Timestamp
        :return:the data recording for the time interval
        :rtype:list
        """

        if timestamps:
            original_list = []
            for the_timestamp in timestamps:
                param = self.generate_request_param(security_item, start, end, size, the_timestamp)
                tmp_list = self.api_wrapper.request(url=self.url, param=param, method=self.request_method,
                                                    path_fields=self.path_fields)
                self.logger.info(
                    "record {} for security_id:{},timestamp:{}".format(
                        self.data_schema, security_item.id, the_timestamp))
                # fill timestamp field
                for tmp in tmp_list:
                    tmp[self.get_timestamp_field()] = the_timestamp
                original_list += tmp_list
                if len(original_list) == self.batch_size:
                    break
            return original_list

        else:
            param = self.generate_request_param(security_item, start, end, size, None)
            return self.api_wrapper.request(url=self.url, param=param, method=self.request_method,
                                            path_fields=self.path_fields)

    def get_timestamp_field(self):
        return 'timestamp'

    def generate_domain_id(self, security_item, original_data):
        timestamp = original_data[self.get_timestamp_field()]
        return "{}_{}".format(security_item.id, timestamp)

    def generate_domain(self, security_item, original_data):
        """
        generate the data_schema instance using security_item and original_data,the original_data should be from record

        :param security_item:
        :param original_data:
        """
        the_id = self.generate_domain_id(security_item, original_data)

        items = get_data(data_schema=self.data_schema, session=self.session, provider=self.provider,
                         security_id=security_item.id,
                         filters=[self.data_schema.id == the_id],
                         return_type='domain')

        if items and not self.force_update:
            self.logger.info('ignore the data {}:{} saved before'.format(self.data_schema, the_id))
            return None

        if not items:
            timestamp_str = original_data[self.get_timestamp_field()]
            timestamp = None
            try:
                timestamp = to_pd_timestamp(timestamp_str)
            except Exception as e:
                self.logger.exception(e)

            domain_item = self.data_schema(id=the_id,
                                           code=security_item.code,
                                           security_id=security_item.id,
                                           timestamp=timestamp)
        else:
            domain_item = items[0]

        fill_domain_from_dict(domain_item, original_data, self.get_data_map())
        return domain_item

    def persist(self, security_item, domain_list):
        """
        persist the domain list to db

        :param security_item:
        :param domain_list:
        """
        if domain_list:
            first_timestamp = domain_list[0].timestamp
            last_timestamp = domain_list[-1].timestamp
            self.logger.info(
                "persist {} for security_id:{},time interval:[{},{}]".format(
                    self.data_schema, security_item.id, first_timestamp, last_timestamp))

            self.session.add_all(domain_list)
            self.session.commit()

    def on_stop(self):
        self.session.close()

    def on_finish(self, security_item):
        pass

    def run(self):
        finished_items = []
        unfinished_items = self.securities
        while True:
            for security_item in unfinished_items:
                try:
                    latest_timestamp, end_timestamp, size, timestamps = self.evaluate_start_end_size_timestamps(
                        security_item)

                    self.logger.info(
                        'security_id:{},evaluate_start_end_size_timestamps result:{},{},{},{}'.format(security_item.id,
                                                                                                      latest_timestamp,
                                                                                                      end_timestamp,
                                                                                                      size, timestamps))

                    # no more to record
                    if size == 0:
                        finished_items.append(security_item)
                        self.logger.info(
                            "finish recording {} for security_id:{},latest_timestamp:{}".format(
                                self.data_schema,
                                security_item.id,
                                latest_timestamp))
                        self.on_finish(security_item)
                        continue

                    original_list = self.record(security_item, start=latest_timestamp, end=end_timestamp, size=size,
                                                timestamps=timestamps)

                    if original_list:
                        domain_list = []
                        duplicate_count = 0
                        for original_item in original_list:
                            domain_item = self.generate_domain(security_item, original_item)
                            # handle the case  generate_domain_id generate duplicate id
                            if domain_item:
                                duplicate = [item for item in domain_list if item.id == domain_item.id]
                                if duplicate:
                                    duplicate_count += 1
                                    domain_item.id = "{}_{}".format(domain_item.id, duplicate_count)

                                domain_list.append(domain_item)

                        if domain_list:
                            self.persist(security_item, domain_list)
                        else:
                            self.logger.info('just get {} duplicated data in this cycle'.format(len(original_list)))

                    # no  more data or force set to one shot means finished
                    if not original_list or self.one_shot:
                        finished_items.append(security_item)
                        self.logger.info(
                            "finish recording {} for security_id:{},latest_timestamp:{}".format(
                                self.data_schema,
                                security_item.id,
                                latest_timestamp))
                        self.on_finish(security_item)
                        continue

                    time.sleep(self.sleeping_time)
                except Exception as e:
                    self.logger.exception(
                        "recording data for security_id:{},{},error:{}".format(security_item.id, self.data_schema, e))
                    finished_items = unfinished_items
                    break

            unfinished_items = set(unfinished_items) - set(finished_items)

            if len(unfinished_items) == 0:
                break

        self.on_stop()


class FixedCycleDataRecorder(TimeSeriesDataRecorder):

    def __init__(self, security_type=SecurityType.stock, exchanges=['sh', 'sz'], codes=None, batch_size=10,
                 force_update=False, sleeping_time=5, fetching_style=TimeSeriesFetchingStyle.end_size,
                 default_size=2000, contain_unfinished_data=False, level=TradingLevel.LEVEL_1DAY,
                 one_shot=False, kdata_use_begin_time=False) -> None:
        super().__init__(security_type, exchanges, codes, batch_size, force_update, sleeping_time, fetching_style,
                         default_size, one_shot)

        self.level = level
        # FIXME:should remove unfinished data when recording,always set it to False now
        self.contain_unfinished_data = contain_unfinished_data
        self.kdata_use_begin_time = kdata_use_begin_time

    def evaluate_start_end_size_timestamps(self, security_item):
        """
        evaluate the size for recording data
        :param security_item:
        :type security_item: str
        :return:the start,end,size need to recording,size=0 means finish recording
        :rtype:(pd.Timestamp,pd.Timestamp,int)
        """

        # get latest record
        latest_record = get_data(security_id=security_item.id,
                                 provider=self.provider,
                                 data_schema=self.data_schema, level=self.level.value,
                                 order=self.data_schema.timestamp.desc(), limit=1,
                                 return_type='domain',
                                 session=self.session)

        if latest_record:
            latest_timestamp = latest_record[0].timestamp
        else:
            latest_timestamp = security_item.timestamp

        if not latest_timestamp:
            return latest_timestamp, None, self.default_size, None

        current_time = pd.Timestamp.now()
        time_delta = current_time - latest_timestamp

        if self.level == TradingLevel.LEVEL_1DAY:
            if is_same_date(current_time, latest_timestamp):
                return latest_timestamp, None, 0, None
            return latest_timestamp, None, time_delta.days + 1, None

        close_hour, close_minute = get_close_time(security_item.id)

        # to today,check closing time
        # 0,0 means never stop,e.g,coin
        if (close_hour != 0 and close_minute != 0) and time_delta.days == 0:
            if latest_timestamp.hour == close_hour and latest_timestamp.minute == close_minute:
                return latest_timestamp, None, 0, None

        if self.kdata_use_begin_time:
            touching_timestamp = latest_timestamp + pd.Timedelta(seconds=self.level.to_second())
        else:
            touching_timestamp = latest_timestamp

        waiting_seconds, size = self.level.count_from_timestamp(touching_timestamp,
                                                                one_day_trading_minutes=get_one_day_trading_minutes(
                                                                    security_item.id))
        if not self.one_shot and waiting_seconds and (waiting_seconds > 30):
            t = waiting_seconds / 2
            self.logger.info(
                'level:{},recorded_time:{},touching_timestamp:{},current_time:{},next_ok_time:{},just sleep:{} seconds'.format(
                    self.level.value,
                    latest_timestamp,
                    touching_timestamp,
                    current_time,
                    touching_timestamp + pd.Timedelta(
                        seconds=self.level.to_second()),
                    t))
            time.sleep(t)

        return latest_timestamp, None, size, None

    def persist(self, security_item, domain_list):
        if domain_list:
            first_timestamp = domain_list[0].timestamp
            last_timestamp = domain_list[-1].timestamp
            self.logger.info(
                "recording {} for security_id:{},level:{},first_timestamp:{},last_timestamp:{}".format(
                    self.data_schema, security_item.id, self.level, first_timestamp, last_timestamp))

            current_timestamp = now_pd_timestamp()

            saving_datas = domain_list

            # FIXME:remove this logic
            # FIXME:should remove unfinished data when recording,always set it to False now
            if is_same_date(current_timestamp, last_timestamp) and self.contain_unfinished_data:
                close_hour, close_minute = get_close_time(security_item.id)
                if current_timestamp.hour >= close_hour and current_timestamp.minute >= close_minute + 2:
                    # after the closing time of the day,we think the last data is finished
                    saving_datas = domain_list
                else:
                    # ignore unfinished kdata
                    saving_datas = domain_list[:-1]
                    self.logger.info(
                        "ignore kdata for security_id:{},level:{},timestamp:{},current_timestamp".format(
                            security_item.id,
                            self.level,
                            last_timestamp, current_timestamp))

            self.session.add_all(saving_datas)
            self.session.commit()


class TimestampsDataRecorder(TimeSeriesDataRecorder):

    def __init__(self, security_type=SecurityType.stock, exchanges=['sh', 'sz'], codes=None, batch_size=10,
                 force_update=False, sleeping_time=5, fetching_style=TimeSeriesFetchingStyle.end_size,
                 default_size=2000) -> None:
        super().__init__(security_type, exchanges, codes, batch_size, force_update, sleeping_time, fetching_style,
                         default_size)
        self.security_timestamps_map = {}

    def init_timestamps(self, security_item):
        """
        overwrite this function to init the timestamps in self.security_timestamps_map

        :param security_item:
        :type security_item:
        """
        raise NotImplementedError

    def evaluate_start_end_size_timestamps(self, security_item):
        the_timestamps = self.security_timestamps_map.get(security_item.id)
        if not the_timestamps:
            self.init_timestamps(security_item)
            the_timestamps = self.security_timestamps_map.get(security_item.id)

        if not the_timestamps:
            self.logger.exception("could not get time series for:{}".format(security_item.id))
            assert False

        timestamps = [to_pd_timestamp(t) for t in the_timestamps]
        timestamps.sort()

        self.logger.info(
            'security_id:{},init timestamps start:{},end:{}'.format(security_item.id, timestamps[0], timestamps[-1]))

        latest_record = get_data(security_id=security_item.id,
                                 provider=self.provider,
                                 data_schema=self.data_schema,
                                 order=self.data_schema.timestamp.desc(), limit=1,
                                 return_type='domain',
                                 session=self.session)

        if latest_record:
            self.logger.info('latest record timestamp:{}'.format(latest_record[0].timestamp))
            timestamps = [t for t in timestamps if t > latest_record[0].timestamp]

            if timestamps:
                return timestamps[0], timestamps[-1], len(timestamps), timestamps
            return None, None, 0, None

        return timestamps[0], timestamps[-1], len(timestamps), timestamps
