# -*- coding: utf-8 -*-
import logging
import time
import uuid
from typing import List

import pandas as pd
from sqlalchemy.orm import Session

from zvt.contract import IntervalLevel
from zvt.contract.api import get_db_session, get_schema_columns
from zvt.contract.api import get_entities, get_data
from zvt.contract.base import StatefulService
from zvt.contract.schema import Mixin, TradableEntity
from zvt.contract.zvt_info import RecorderState
from zvt.utils import pd_is_not_null
from zvt.utils.time_utils import (
    to_pd_timestamp,
    TIME_FORMAT_DAY,
    to_time_str,
    evaluate_size_from_timestamp,
    is_in_same_interval,
    now_pd_timestamp,
    now_time_str,
)
from zvt.utils.utils import fill_domain_from_dict


class Meta(type):
    def __new__(meta, name, bases, class_dict):
        cls = type.__new__(meta, name, bases, class_dict)
        # register the recorder class to the data_schema
        if hasattr(cls, "data_schema") and hasattr(cls, "provider"):
            if cls.data_schema and issubclass(cls.data_schema, Mixin):
                print(f"{cls.__name__}:{cls.data_schema.__name__}")
                cls.data_schema.register_recorder_cls(cls.provider, cls)
        return cls


class Recorder(StatefulService, metaclass=Meta):
    # overwrite them to setup the data you want to record
    provider: str = None
    data_schema: Mixin = None

    # original page url
    original_page_url = None
    # request url
    url = None

    state_schema = RecorderState

    def __init__(self, force_update: bool = False, sleeping_time: int = 10) -> None:
        super().__init__()
        self.logger = logging.getLogger(self.__class__.__name__)

        assert self.provider is not None
        assert self.data_schema is not None
        if self.provider not in self.data_schema.providers:
            self.logger.error(
                f"provider: {self.provider} is not registered for {self.data_schema}({self.data_schema.providers})"
            )
            assert False

        self.force_update = force_update
        self.sleeping_time = sleeping_time

        # using to do db operations
        self.session = get_db_session(provider=self.provider, data_schema=self.data_schema)

    def run(self):
        raise NotImplementedError

    def sleep(self, seconds=None):
        if seconds:
            sleeping_time = seconds
        else:
            sleeping_time = self.sleeping_time

        if sleeping_time and sleeping_time > 0:
            self.logger.info(f"sleeping {sleeping_time} seconds")
            time.sleep(self.sleeping_time)


class EntityEventRecorder(Recorder):
    # overwrite them to fetch the entity list
    entity_provider: str = None
    entity_schema: TradableEntity = None

    def __init__(
        self,
        force_update=False,
        sleeping_time=10,
        exchanges=None,
        entity_ids=None,
        code=None,
        codes=None,
        day_data=False,
        entity_filters=None,
        ignore_failed=True,
    ) -> None:
        """
        :param code:
        :param ignore_failed:
        :param entity_filters:
        :param exchanges:
        :param entity_ids: set entity_ids or (entity_type,exchanges,codes)
        :param codes:
        :param day_data: one record per day,set to True if you want skip recording it when data of today exist
        :param force_update:
        :param sleeping_time:
        """
        super().__init__(force_update=force_update, sleeping_time=sleeping_time)

        assert self.entity_provider is not None
        assert self.entity_schema is not None

        # setup the entities you want to record
        self.exchanges = exchanges
        if codes is None and code is not None:
            self.codes = [code]
        else:
            self.codes = codes
        self.day_data = day_data

        # set entity_ids or (entity_type,exchanges,codes)
        self.entity_ids = entity_ids
        self.entity_filters = entity_filters
        self.ignore_failed = ignore_failed

        self.entity_session: Session = None
        self.entities: List = None
        self.init_entities()

    def init_entities(self):
        """
        init the entities which we would record data for

        """
        if self.entity_provider == self.provider and self.entity_schema == self.data_schema:
            self.entity_session = self.session
        else:
            self.entity_session = get_db_session(provider=self.entity_provider, data_schema=self.entity_schema)

        if self.day_data:
            df = self.data_schema.query_data(
                start_timestamp=now_time_str(), columns=["entity_id", "timestamp"], provider=self.provider
            )
            if pd_is_not_null(df):
                entity_ids = df["entity_id"].tolist()
                self.logger.info(f"ignore entity_ids:{entity_ids}")
                if self.entity_filters:
                    self.entity_filters.append(self.entity_schema.entity_id.notin_(entity_ids))
                else:
                    self.entity_filters = [self.entity_schema.entity_id.notin_(entity_ids)]

        # init the entity list
        self.entities = get_entities(
            session=self.entity_session,
            entity_schema=self.entity_schema,
            exchanges=self.exchanges,
            entity_ids=self.entity_ids,
            codes=self.codes,
            return_type="domain",
            provider=self.entity_provider,
            filters=self.entity_filters,
        )


class TimeSeriesDataRecorder(EntityEventRecorder):
    default_size = 2000

    def __init__(
        self,
        force_update=False,
        sleeping_time=5,
        exchanges=None,
        entity_ids=None,
        code=None,
        codes=None,
        day_data=False,
        entity_filters=None,
        ignore_failed=True,
        real_time=False,
        fix_duplicate_way="add",
        start_timestamp=None,
        end_timestamp=None,
    ) -> None:
        super().__init__(
            force_update,
            sleeping_time,
            exchanges,
            entity_ids,
            code=code,
            codes=codes,
            day_data=day_data,
            entity_filters=entity_filters,
            ignore_failed=ignore_failed,
        )

        self.real_time = real_time
        self.close_hour, self.close_minute = self.entity_schema.get_close_hour_and_minute()
        self.fix_duplicate_way = fix_duplicate_way
        self.start_timestamp = to_pd_timestamp(start_timestamp)
        self.end_timestamp = to_pd_timestamp(end_timestamp)

    def get_latest_saved_record(self, entity):
        order = eval("self.data_schema.{}.desc()".format(self.get_evaluated_time_field()))

        records = get_data(
            entity_id=entity.id,
            provider=self.provider,
            data_schema=self.data_schema,
            order=order,
            limit=1,
            return_type="domain",
            session=self.session,
        )
        if records:
            return records[0]
        return None

    def evaluate_start_end_size_timestamps(self, entity):
        # not to list date yet
        if entity.timestamp and (entity.timestamp >= now_pd_timestamp()):
            self.logger.info("ignore entity: {} list date: {}", entity.id, entity.timestamp)
            return entity.timestamp, None, 0, None

        latest_saved_record = self.get_latest_saved_record(entity=entity)

        if latest_saved_record:
            latest_timestamp = eval("latest_saved_record.{}".format(self.get_evaluated_time_field()))
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
        return {}

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
        return "timestamp"

    def get_original_time_field(self):
        return "timestamp"

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

        got_new_data = False

        # if the domain is directly generated in record method, we just return it
        if isinstance(original_data, self.data_schema):
            got_new_data = True
            return got_new_data, original_data

        the_id = self.generate_domain_id(entity, original_data)

        # optional way
        # item = self.session.query(self.data_schema).get(the_id)

        items = get_data(
            data_schema=self.data_schema,
            session=self.session,
            provider=self.provider,
            entity_id=entity.id,
            filters=[self.data_schema.id == the_id],
            return_type="domain",
        )

        if items and not self.force_update:
            self.logger.info("ignore the data {}:{} saved before".format(self.data_schema, the_id))
            return got_new_data, None

        if not items:
            timestamp_str = original_data[self.get_original_time_field()]
            timestamp = None
            try:
                timestamp = to_pd_timestamp(timestamp_str)
            except Exception as e:
                self.logger.exception(e)

            if "name" in get_schema_columns(self.data_schema):
                domain_item = self.data_schema(
                    id=the_id, code=entity.code, name=entity.name, entity_id=entity.id, timestamp=timestamp
                )
            else:
                domain_item = self.data_schema(id=the_id, code=entity.code, entity_id=entity.id, timestamp=timestamp)
            got_new_data = True
        else:
            domain_item = items[0]

        fill_domain_from_dict(domain_item, original_data, self.get_data_map())
        return got_new_data, domain_item

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
                    self.data_schema, entity.id, first_timestamp, last_timestamp
                )
            )

            self.session.add_all(domain_list)
            self.session.commit()

    def on_finish(self):
        try:
            if self.session:
                self.session.close()

            if self.entity_session:
                self.entity_session.close()
        except Exception as e:
            self.logger.error(e)

    def on_finish_entity(self, entity):
        pass

    def run(self):
        finished_items = []
        unfinished_items = self.entities
        raising_exception = None
        while True:
            count = len(unfinished_items)
            for index, entity_item in enumerate(unfinished_items):
                try:
                    self.logger.info(f"run to {index + 1}/{count}")

                    start_timestamp, end_timestamp, size, timestamps = self.evaluate_start_end_size_timestamps(
                        entity_item
                    )
                    size = int(size)

                    if timestamps:
                        self.logger.info(
                            "entity_id:{},evaluate_start_end_size_timestamps result:{},{},{},{}-{}".format(
                                entity_item.id, start_timestamp, end_timestamp, size, timestamps[0], timestamps[-1]
                            )
                        )
                    else:
                        self.logger.info(
                            "entity_id:{},evaluate_start_end_size_timestamps result:{},{},{},{}".format(
                                entity_item.id, start_timestamp, end_timestamp, size, timestamps
                            )
                        )

                    # no more to record
                    if size == 0:
                        finished_items.append(entity_item)
                        self.logger.info(
                            "finish recording {} for entity_id:{},latest_timestamp:{}".format(
                                self.data_schema, entity_item.id, start_timestamp
                            )
                        )
                        self.on_finish_entity(entity_item)
                        continue

                    # sleep for a while to next entity
                    if index != 0:
                        self.sleep()

                    original_list = self.record(
                        entity_item, start=start_timestamp, end=end_timestamp, size=size, timestamps=timestamps
                    )

                    all_duplicated = True

                    if original_list:
                        domain_list = []
                        for original_item in original_list:
                            got_new_data, domain_item = self.generate_domain(entity_item, original_item)

                            if got_new_data:
                                all_duplicated = False

                            # handle the case  generate_domain_id generate duplicate id
                            if domain_item:
                                duplicate = [item for item in domain_list if item.id == domain_item.id]
                                if duplicate:
                                    # regenerate the id
                                    if self.fix_duplicate_way == "add":
                                        domain_item.id = "{}_{}".format(domain_item.id, uuid.uuid1())
                                    # ignore
                                    else:
                                        self.logger.info(f"ignore original duplicate item:{domain_item.id}")
                                        continue

                                domain_list.append(domain_item)

                        if domain_list:
                            self.persist(entity_item, domain_list)
                        else:
                            self.logger.info("just got {} duplicated data in this cycle".format(len(original_list)))

                    # could not get more data
                    entity_finished = False
                    if not original_list or all_duplicated:
                        # not realtime
                        if not self.real_time:
                            entity_finished = True

                        # realtime and to the close time
                        if self.real_time and (self.close_hour is not None) and (self.close_minute is not None):
                            current_timestamp = pd.Timestamp.now()
                            if current_timestamp.hour >= self.close_hour:
                                if current_timestamp.minute - self.close_minute >= 5:
                                    self.logger.info(
                                        "{} now is the close time:{}".format(entity_item.id, current_timestamp)
                                    )

                                    entity_finished = True

                    # add finished entity to finished_items
                    if entity_finished:
                        finished_items.append(entity_item)

                        latest_saved_record = self.get_latest_saved_record(entity=entity_item)
                        if latest_saved_record:
                            start_timestamp = eval("latest_saved_record.{}".format(self.get_evaluated_time_field()))

                        self.logger.info(
                            "finish recording {} for entity_id:{},latest_timestamp:{}".format(
                                self.data_schema, entity_item.id, start_timestamp
                            )
                        )
                        self.on_finish_entity(entity_item)
                        continue

                except Exception as e:
                    self.logger.exception(
                        "recording data for entity_id:{},{},error:{}".format(entity_item.id, self.data_schema, e)
                    )
                    raising_exception = e
                    finished_items = unfinished_items
                    break

            unfinished_items = set(unfinished_items) - set(finished_items)

            if len(unfinished_items) == 0:
                break

        self.on_finish()

        if raising_exception:
            raise raising_exception


class FixedCycleDataRecorder(TimeSeriesDataRecorder):
    def __init__(
        self,
        force_update=True,
        sleeping_time=10,
        exchanges=None,
        entity_ids=None,
        code=None,
        codes=None,
        day_data=False,
        entity_filters=None,
        ignore_failed=True,
        real_time=False,
        fix_duplicate_way="ignore",
        start_timestamp=None,
        end_timestamp=None,
        level=IntervalLevel.LEVEL_1DAY,
        kdata_use_begin_time=False,
        one_day_trading_minutes=24 * 60,
    ) -> None:
        super().__init__(
            force_update,
            sleeping_time,
            exchanges,
            entity_ids,
            code=code,
            codes=codes,
            day_data=day_data,
            entity_filters=entity_filters,
            ignore_failed=ignore_failed,
            real_time=real_time,
            fix_duplicate_way=fix_duplicate_way,
            start_timestamp=start_timestamp,
            end_timestamp=end_timestamp,
        )

        self.level = IntervalLevel(level)
        self.kdata_use_begin_time = kdata_use_begin_time
        self.one_day_trading_minutes = one_day_trading_minutes

    def get_latest_saved_record(self, entity):
        order = eval("self.data_schema.{}.desc()".format(self.get_evaluated_time_field()))

        # 对于k线这种数据，最后一个记录有可能是没完成的，所以取两个
        # 同一周期内只保留最新的一个数据
        records = get_data(
            entity_id=entity.id,
            provider=self.provider,
            data_schema=self.data_schema,
            order=order,
            limit=2,
            return_type="domain",
            session=self.session,
            level=self.level,
        )
        if records:
            # delete unfinished kdata
            if len(records) == 2:
                if is_in_same_interval(t1=records[0].timestamp, t2=records[1].timestamp, level=self.level):
                    self.session.delete(records[1])
                    self.session.flush()
            return records[0]
        return None

    def evaluate_start_end_size_timestamps(self, entity):
        # not to list date yet
        if entity.timestamp and (entity.timestamp >= now_pd_timestamp()):
            return entity.timestamp, None, 0, None

        # get latest record
        latest_saved_record = self.get_latest_saved_record(entity=entity)

        if latest_saved_record:
            # the latest saved timestamp
            latest_saved_timestamp = latest_saved_record.timestamp
        else:
            # the list date
            latest_saved_timestamp = entity.timestamp

        if not latest_saved_timestamp:
            return None, None, self.default_size, None

        size = evaluate_size_from_timestamp(
            start_timestamp=latest_saved_timestamp,
            level=self.level,
            one_day_trading_minutes=self.one_day_trading_minutes,
        )

        if self.start_timestamp:
            start = max(self.start_timestamp, latest_saved_timestamp)
        else:
            start = latest_saved_timestamp

        return start, None, size, None


class TimestampsDataRecorder(TimeSeriesDataRecorder):
    def __init__(
        self,
        force_update=False,
        sleeping_time=5,
        exchanges=None,
        entity_ids=None,
        code=None,
        codes=None,
        day_data=False,
        entity_filters=None,
        ignore_failed=True,
        real_time=False,
        fix_duplicate_way="add",
        start_timestamp=None,
        end_timestamp=None,
    ) -> None:
        super().__init__(
            force_update,
            sleeping_time,
            exchanges,
            entity_ids,
            code=code,
            codes=codes,
            day_data=day_data,
            entity_filters=entity_filters,
            ignore_failed=ignore_failed,
            real_time=real_time,
            fix_duplicate_way=fix_duplicate_way,
            start_timestamp=start_timestamp,
            end_timestamp=end_timestamp,
        )
        self.security_timestamps_map = {}

    def init_timestamps(self, entity_item) -> List[pd.Timestamp]:
        raise NotImplementedError

    def evaluate_start_end_size_timestamps(self, entity):
        timestamps = self.security_timestamps_map.get(entity.id)
        if not timestamps:
            timestamps = self.init_timestamps(entity)
            if self.start_timestamp:
                timestamps = [t for t in timestamps if t >= self.start_timestamp]

            if self.end_timestamp:
                timestamps = [t for t in timestamps if t <= self.end_timestamp]

            self.security_timestamps_map[entity.id] = timestamps

        if not timestamps:
            return None, None, 0, timestamps

        timestamps.sort()

        self.logger.info("entity_id:{},timestamps start:{},end:{}".format(entity.id, timestamps[0], timestamps[-1]))

        latest_record = self.get_latest_saved_record(entity=entity)

        if latest_record:
            self.logger.info("latest record timestamp:{}".format(latest_record.timestamp))
            timestamps = [t for t in timestamps if t >= latest_record.timestamp]

            if timestamps:
                return timestamps[0], timestamps[-1], len(timestamps), timestamps
            return None, None, 0, None

        return timestamps[0], timestamps[-1], len(timestamps), timestamps


# the __all__ is generated
__all__ = [
    "Meta",
    "Recorder",
    "EntityEventRecorder",
    "TimeSeriesDataRecorder",
    "FixedCycleDataRecorder",
    "TimestampsDataRecorder",
]
