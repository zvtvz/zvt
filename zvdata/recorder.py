# -*- coding: utf-8 -*-
import logging
import time
from typing import List

import pandas as pd
from sqlalchemy.orm import Session

from zvdata.api import get_entities, get_data
from zvdata.domain import get_db_session
from zvdata.structs import IntervalLevel
from zvdata.utils.time_utils import is_same_date, now_pd_timestamp, to_pd_timestamp, TIME_FORMAT_DAY, to_time_str
from zvdata.utils.utils import fill_domain_from_dict


class Recorder(object):
    logger = logging.getLogger(__name__)

    # overwrite them to setup the data you want to record
    provider: str = None
    data_schema = None

    url = None

    def __init__(self,
                 batch_size: int = 10,
                 force_update: bool = False,
                 sleeping_time: int = 10) -> None:
        """

        :param batch_size:batch size to saving to db
        :type batch_size:int
        :param force_update: whether force update the data even if it exists,please set it to True if the data need to
        be refreshed from the provider
        :type force_update:bool
        :param sleeping_time:sleeping seconds for recoding loop
        :type sleeping_time:int
        """

        assert self.provider is not None
        assert self.data_schema is not None

        self.batch_size = batch_size
        self.force_update = force_update
        self.sleeping_time = sleeping_time

        # using to do db operations
        self.session = get_db_session(provider=self.provider,
                                      data_schema=self.data_schema)

    def run(self):
        raise NotImplementedError

    def sleep(self):
        time.sleep(self.sleeping_time)


class RecorderForEntities(Recorder):
    # overwrite them to fetch the entity list
    entity_provider: str = None
    entity_schema = None

    def __init__(self,
                 entity_type='stock',
                 exchanges=['sh', 'sz'],
                 entity_ids=None,
                 codes=None,
                 batch_size=10,
                 force_update=False,
                 sleeping_time=10) -> None:
        """

        :param entity_type:
        :type entity_type:
        :param exchanges:
        :type exchanges:
        :param entity_ids: set entity_ids or (entity_type,exchanges,codes)
        :type entity_ids:
        :param codes:
        :type codes:
        :param batch_size:
        :type batch_size:
        :param force_update:
        :type force_update:
        :param sleeping_time:
        :type sleeping_time:
        """
        super().__init__(batch_size=batch_size, force_update=force_update, sleeping_time=sleeping_time)

        assert self.entity_provider is not None
        assert self.entity_schema is not None

        # setup the entities you want to record
        self.entity_type = entity_type
        self.exchanges = exchanges
        self.codes = codes

        # set entity_ids or (entity_type,exchanges,codes)
        self.entity_ids = entity_ids

        self.entity_session: Session = None
        self.entities: List = None
        self.init_entities()

    def init_entities(self):
        if self.entity_provider == self.provider and self.entity_schema == self.data_schema:
            self.entity_session = self.session
        else:
            self.entity_session = get_db_session(provider=self.entity_provider, data_schema=self.entity_schema)

        # init the entity list
        self.entities = get_entities(session=self.entity_session,
                                     entity_type=self.entity_type,
                                     exchanges=self.exchanges,
                                     entity_ids=self.entity_ids,
                                     codes=self.codes,
                                     return_type='domain',
                                     provider=self.entity_provider)


class TimeSeriesDataRecorder(RecorderForEntities):
    def __init__(self,
                 entity_type='stock',
                 exchanges=['sh', 'sz'],
                 entity_ids=None,
                 codes=None,
                 batch_size=10,
                 force_update=False,
                 sleeping_time=5,
                 default_size=2000,
                 one_shot=False,
                 fix_duplicate_way='add',
                 start_timestamp=None,
                 end_timestamp=None) -> None:

        self.default_size = default_size
        self.one_shot = one_shot
        self.fix_duplicate_way = fix_duplicate_way

        self.start_timestamp = to_pd_timestamp(start_timestamp)
        self.end_timestamp = to_pd_timestamp(end_timestamp)

        super().__init__(entity_type, exchanges, entity_ids, codes, batch_size, force_update, sleeping_time)

    def get_latest_saved_record(self, entity):
        order = eval('self.data_schema.{}.desc()'.format(self.get_evaluated_time_field()))

        return get_data(entity_id=entity.id,
                        provider=self.provider,
                        data_schema=self.data_schema,
                        order=order,
                        limit=1,
                        return_type='domain',
                        session=self.session)

    def evaluate_start_end_size_timestamps(self, entity):
        latest_saved_record = self.get_latest_saved_record(entity=entity)

        if latest_saved_record:
            latest_timestamp = eval('latest_saved_record[0].{}'.format(self.get_evaluated_time_field()))
        else:
            latest_timestamp = entity.timestamp

        if not latest_timestamp:
            return self.start_timestamp, self.end_timestamp, self.default_size, None

        if self.start_timestamp:
            latest_timestamp = max(latest_timestamp, self.start_timestamp)

        size = self.default_size
        if self.end_timestamp:
            if latest_timestamp > self.end_timestamp:
                size = 0

        return latest_timestamp, self.end_timestamp, size, None

    def get_data_map(self):
        """
        {'original_field':('domain_field',transform_func)}

        """
        raise NotImplementedError

    def record(self, entity, start, end, size, timestamps):
        """
        implement the recording logic in this method, should return json or domain list

        :param entity:
        :type entity:
        :param start:
        :type start:
        :param end:
        :type end:
        :param size:
        :type size:
        :param timestamps:
        :type timestamps:
        """
        raise NotImplementedError

    def get_evaluated_time_field(self):
        """
        the timestamp field for evaluating time range of recorder,used in get_latest_saved_record

        """
        return 'timestamp'

    def get_original_time_field(self):
        return 'timestamp'

    def generate_domain_id(self, entity, original_data, time_fmt=TIME_FORMAT_DAY):
        """
        generate domain id from the entity and original data,the default id meaning:entity + event happen time

        :param entity:
        :type entity:
        :param original_data:
        :type original_data:
        :param time_fmt:
        :type time_fmt:
        :return:
        :rtype:
        """
        timestamp = to_time_str(original_data[self.get_original_time_field()], fmt=time_fmt)
        return "{}_{}".format(entity.id, timestamp)

    def generate_domain(self, entity, original_data):
        """
        generate the data_schema instance using entity and original_data,the original_data is from record result

        :param entity:
        :param original_data:
        """

        # if the domain is directly generated in record method, we just return it
        if isinstance(original_data, self.data_schema):
            return original_data

        the_id = self.generate_domain_id(entity, original_data)

        items = get_data(data_schema=self.data_schema, session=self.session, provider=self.provider,
                         entity_id=entity.id, filters=[self.data_schema.id == the_id], return_type='domain')

        if items and not self.force_update:
            self.logger.info('ignore the data {}:{} saved before'.format(self.data_schema, the_id))
            return None

        if not items:
            timestamp_str = original_data[self.get_original_time_field()]
            timestamp = None
            try:
                timestamp = to_pd_timestamp(timestamp_str)
            except Exception as e:
                self.logger.exception(e)

            domain_item = self.data_schema(id=the_id,
                                           code=entity.code,
                                           entity_id=entity.id,
                                           timestamp=timestamp)
        else:
            domain_item = items[0]

        fill_domain_from_dict(domain_item, original_data, self.get_data_map())
        return domain_item

    def persist(self, entity, domain_list):
        """
        persist the domain list to db

        :param entity:
        :param domain_list:
        """
        if domain_list:
            try:
                if domain_list[0].timestamp >= domain_list[-1].timestamp:
                    first_timestamp = domain_list[-1].timestamp
                    last_timestamp = domain_list[0].timestamp
                else:
                    first_timestamp = domain_list[0].timestamp
                    last_timestamp = domain_list[-1].timestamp
            except:
                first_timestamp = domain_list[0].timestamp
                last_timestamp = domain_list[-1].timestamp

            self.logger.info(
                "persist {} for entity_id:{},time interval:[{},{}]".format(
                    self.data_schema, entity.id, first_timestamp, last_timestamp))

            self.session.add_all(domain_list)
            self.session.commit()

    def on_finish(self):
        self.session.close()

    def on_finish_entity(self, entity):
        pass

    def run(self):
        finished_items = []
        unfinished_items = self.entities
        raising_exeption = None
        while True:
            for entity_item in unfinished_items:
                try:
                    latest_timestamp, end_timestamp, size, timestamps = self.evaluate_start_end_size_timestamps(
                        entity_item)

                    if timestamps:
                        self.logger.info('entity_id:{},evaluate_start_end_size_timestamps result:{},{},{},{}-{}'.format(
                            entity_item.id,
                            latest_timestamp,
                            end_timestamp,
                            size,
                            timestamps[0],
                            timestamps[-1]))
                    else:
                        self.logger.info('entity_id:{},evaluate_start_end_size_timestamps result:{},{},{},{}'.format(
                            entity_item.id,
                            latest_timestamp,
                            end_timestamp,
                            size,
                            timestamps))

                    # no more to record
                    if size == 0:
                        finished_items.append(entity_item)
                        self.logger.info(
                            "finish recording {} for entity_id:{},latest_timestamp:{}".format(
                                self.data_schema,
                                entity_item.id,
                                latest_timestamp))
                        self.on_finish_entity(entity_item)
                        continue

                    original_list = self.record(entity_item, start=latest_timestamp, end=end_timestamp, size=size,
                                                timestamps=timestamps)

                    if original_list:
                        domain_list = []
                        duplicate_count = 0
                        for original_item in original_list:
                            domain_item = self.generate_domain(entity_item, original_item)
                            # handle the case  generate_domain_id generate duplicate id
                            if domain_item:
                                duplicate = [item for item in domain_list if item.id == domain_item.id]
                                if duplicate:
                                    # regenerate the id
                                    if self.fix_duplicate_way == 'add':
                                        duplicate_count += 1
                                        domain_item.id = "{}_{}".format(domain_item.id, duplicate_count)
                                    # ignore
                                    else:
                                        continue

                                domain_list.append(domain_item)

                        if domain_list:
                            self.persist(entity_item, domain_list)
                        else:
                            self.logger.info('just get {} duplicated data in this cycle'.format(len(original_list)))

                    # no  more data or force set to one shot means finished
                    if not original_list or self.one_shot:
                        finished_items.append(entity_item)

                        latest_saved_record = self.get_latest_saved_record(entity=entity_item)
                        if latest_saved_record:
                            latest_timestamp = eval('latest_saved_record[0].{}'.format(self.get_evaluated_time_field()))

                        self.logger.info(
                            "finish recording {} for entity_id:{},latest_timestamp:{}".format(
                                self.data_schema,
                                entity_item.id,
                                latest_timestamp))
                        self.on_finish_entity(entity_item)
                        continue

                    time.sleep(self.sleeping_time)
                except Exception as e:
                    self.logger.exception(
                        "recording data for entity_id:{},{},error:{}".format(entity_item.id, self.data_schema, e))
                    raising_exeption = e
                    finished_items = unfinished_items
                    break

            unfinished_items = set(unfinished_items) - set(finished_items)

            if len(unfinished_items) == 0:
                break

        self.on_finish()

        if raising_exeption:
            raise raising_exeption


class FixedCycleDataRecorder(TimeSeriesDataRecorder):
    def __init__(self,
                 entity_type='stock',
                 exchanges=['sh', 'sz'],
                 entity_ids=None,
                 codes=None,
                 batch_size=10,
                 force_update=False,
                 sleeping_time=10,
                 default_size=2000,
                 one_shot=False,
                 fix_duplicate_way='add',
                 start_timestamp=None,
                 end_timestamp=None,
                 contain_unfinished_data=False,
                 level=IntervalLevel.LEVEL_1DAY,
                 kdata_use_begin_time=False,
                 close_hour=0,
                 close_minute=0,
                 one_day_trading_minutes=24 * 60) -> None:
        super().__init__(entity_type, exchanges, entity_ids, codes, batch_size, force_update, sleeping_time,
                         default_size, one_shot, fix_duplicate_way, start_timestamp, end_timestamp)

        self.level = IntervalLevel(level)
        # FIXME:should remove unfinished data when recording,always set it to False now
        self.contain_unfinished_data = contain_unfinished_data
        self.kdata_use_begin_time = kdata_use_begin_time
        self.close_hour = close_hour
        self.close_minute = close_minute
        self.one_day_trading_minutes = one_day_trading_minutes

    def get_latest_saved_record(self, entity):
        order = eval('self.data_schema.{}.desc()'.format(self.get_evaluated_time_field()))

        return get_data(entity_id=entity.id,
                        provider=self.provider,
                        data_schema=self.data_schema,
                        order=order,
                        limit=1,
                        return_type='domain',
                        session=self.session,
                        level=self.level.value)

    def evaluate_start_end_size_timestamps(self, entity):
        # get latest record
        latest_saved_record = self.get_latest_saved_record(entity=entity)

        if latest_saved_record:
            latest_timestamp = latest_saved_record[0].timestamp
        else:
            latest_timestamp = entity.timestamp

        if not latest_timestamp:
            return latest_timestamp, None, self.default_size, None

        current_time = pd.Timestamp.now()
        time_delta = current_time - latest_timestamp

        if self.level == IntervalLevel.LEVEL_1DAY:
            if is_same_date(current_time, latest_timestamp):
                return latest_timestamp, None, 0, None
            return latest_timestamp, None, time_delta.days + 1, None

        # to today,check closing time
        # 0,0 means never stop,e.g,coin
        if (self.close_hour != 0 and self.close_minute != 0) and time_delta.days == 0:
            if latest_timestamp.hour == self.close_hour and latest_timestamp.minute == self.close_minute:
                return latest_timestamp, None, 0, None

        if self.kdata_use_begin_time:
            touching_timestamp = latest_timestamp + pd.Timedelta(seconds=self.level.to_second())
        else:
            touching_timestamp = latest_timestamp

        waiting_seconds, size = self.level.count_from_timestamp(touching_timestamp,
                                                                one_day_trading_minutes=self.one_day_trading_minutes)
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

    def persist(self, entity, domain_list):
        if domain_list:
            if domain_list[0].timestamp >= domain_list[-1].timestamp:
                first_timestamp = domain_list[-1].timestamp
                last_timestamp = domain_list[0].timestamp
            else:
                first_timestamp = domain_list[0].timestamp
                last_timestamp = domain_list[-1].timestamp

            self.logger.info(
                "persist {} for entity_id:{},time interval:[{},{}]".format(
                    self.data_schema, entity.id, first_timestamp, last_timestamp))

            current_timestamp = now_pd_timestamp()

            saving_datas = domain_list

            # FIXME:remove this logic
            # FIXME:should remove unfinished data when recording,always set it to False now
            if is_same_date(current_timestamp, last_timestamp) and self.contain_unfinished_data:
                if current_timestamp.hour >= self.close_hour and current_timestamp.minute >= self.close_minute + 2:
                    # after the closing time of the day,we think the last data is finished
                    saving_datas = domain_list
                else:
                    # ignore unfinished kdata
                    saving_datas = domain_list[:-1]
                    self.logger.info(
                        "ignore kdata for entity_id:{},level:{},timestamp:{},current_timestamp".format(
                            entity.id,
                            self.level,
                            last_timestamp, current_timestamp))

            self.session.add_all(saving_datas)
            self.session.commit()


class TimestampsDataRecorder(TimeSeriesDataRecorder):

    def __init__(self,
                 entity_type='stock',
                 exchanges=['sh', 'sz'],
                 entity_ids=None,
                 codes=None,
                 batch_size=10,
                 force_update=False,
                 sleeping_time=5,
                 default_size=2000,
                 one_shot=False,
                 fix_duplicate_way='add',
                 start_timestamp=None,
                 end_timestamp=None) -> None:
        super().__init__(entity_type, exchanges, entity_ids, codes, batch_size, force_update, sleeping_time,
                         default_size, one_shot, fix_duplicate_way, start_timestamp, end_timestamp)
        self.security_timestamps_map = {}

    def init_timestamps(self, entity_item) -> List[pd.Timestamp]:
        raise NotImplementedError

    def evaluate_start_end_size_timestamps(self, entity):
        timestamps = self.security_timestamps_map.get(entity.id)
        if not timestamps:
            timestamps = self.init_timestamps(entity)
            self.security_timestamps_map[entity.id] = timestamps

        timestamps.sort()

        self.logger.info(
            'entity_id:{},timestamps start:{},end:{}'.format(entity.id, timestamps[0], timestamps[-1]))

        latest_record = self.get_latest_saved_record(entity=entity)

        if latest_record:
            self.logger.info('latest record timestamp:{}'.format(latest_record[0].timestamp))
            timestamps = [t for t in timestamps if t > latest_record[0].timestamp]

            if timestamps:
                return timestamps[0], timestamps[-1], len(timestamps), timestamps
            return None, None, 0, None

        return timestamps[0], timestamps[-1], len(timestamps), timestamps
