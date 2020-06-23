# -*- coding: utf-8 -*-
import inspect
from datetime import timedelta
from typing import List, Union

import pandas as pd
from sqlalchemy import Column, String, DateTime
from sqlalchemy.orm import Session

from zvt.contract import IntervalLevel
from zvt.utils.time_utils import date_and_time, is_same_time


class Mixin(object):
    id = Column(String, primary_key=True)
    # entity id for this model
    entity_id = Column(String)

    # the meaning could be different for different case,most of time it means 'happen time'
    timestamp = Column(DateTime)

    @classmethod
    def help(cls):
        print(inspect.getsource(cls))

    @classmethod
    def important_cols(cls):
        return []

    @classmethod
    def time_field(cls):
        return 'timestamp'

    @classmethod
    def register_recorder_cls(cls, provider, recorder_cls):
        """
        register the recorder for the schema

        :param provider:
        :param recorder_cls:
        """
        # dont't make provider_map_recorder as class field,it should be created for the sub class as need
        if not hasattr(cls, 'provider_map_recorder'):
            cls.provider_map_recorder = {}

        if provider not in cls.provider_map_recorder:
            cls.provider_map_recorder[provider] = recorder_cls

    @classmethod
    def register_provider(cls, provider):
        # dont't make providers as class field,it should be created for the sub class as need
        if not hasattr(cls, 'providers'):
            cls.providers = []

        if provider not in cls.providers:
            cls.providers.append(provider)

    @classmethod
    def query_data(cls,
                   provider_index: int = 0,
                   ids: List[str] = None,
                   entity_ids: List[str] = None,
                   entity_id: str = None,
                   codes: List[str] = None,
                   code: str = None,
                   level: Union[IntervalLevel, str] = None,
                   provider: str = None,
                   columns: List = None,
                   col_label: dict = None,
                   return_type: str = 'df',
                   start_timestamp: Union[pd.Timestamp, str] = None,
                   end_timestamp: Union[pd.Timestamp, str] = None,
                   filters: List = None,
                   session: Session = None,
                   order=None,
                   limit: int = None,
                   index: Union[str, list] = None,
                   time_field: str = 'timestamp'):
        from .api import get_data
        if not provider:
            provider = cls.providers[provider_index]
        return get_data(data_schema=cls, ids=ids, entity_ids=entity_ids, entity_id=entity_id, codes=codes,
                        code=code, level=level, provider=provider, columns=columns, col_label=col_label,
                        return_type=return_type, start_timestamp=start_timestamp, end_timestamp=end_timestamp,
                        filters=filters, session=session, order=order, limit=limit, index=index, time_field=time_field)

    @classmethod
    def record_data(cls,
                    provider_index: int = 0,
                    provider: str = None,
                    exchanges=None,
                    entity_ids=None,
                    codes=None,
                    batch_size=None,
                    force_update=None,
                    sleeping_time=None,
                    default_size=None,
                    real_time=None,
                    fix_duplicate_way=None,
                    start_timestamp=None,
                    end_timestamp=None,
                    close_hour=None,
                    close_minute=None,
                    one_day_trading_minutes=None):
        if cls.provider_map_recorder:
            print(f'{cls.__name__} registered recorders:{cls.provider_map_recorder}')

            if provider:
                recorder_class = cls.provider_map_recorder[provider]
            else:
                recorder_class = cls.provider_map_recorder[cls.providers[provider_index]]

            # get args for specific recorder class
            from zvt.contract.recorder import TimeSeriesDataRecorder
            if issubclass(recorder_class, TimeSeriesDataRecorder):
                args = [item for item in inspect.getfullargspec(cls.record_data).args if
                        item not in ('cls', 'provider_index', 'provider')]
            else:
                args = ['batch_size', 'force_update', 'sleeping_time']

            # just fill the None arg to kw,so we could use the recorder_class default args
            kw = {}
            for arg in args:
                tmp = eval(arg)
                if tmp is not None:
                    kw[arg] = tmp

            # FixedCycleDataRecorder
            from zvt.contract.recorder import FixedCycleDataRecorder
            if issubclass(recorder_class, FixedCycleDataRecorder):
                # contract:
                # 1)use FixedCycleDataRecorder to record the data with IntervalLevel
                # 2)the table of schema with IntervalLevel format is {entity}_{level}_[adjust_type]_{event}
                table: str = cls.__tablename__
                try:
                    items = table.split('_')
                    if len(items) == 4:
                        adjust_type = items[2]
                        kw['adjust_type'] = adjust_type
                    level = IntervalLevel(items[1])
                except:
                    # for other schema not with normal format,but need to calculate size for remaining days
                    level = IntervalLevel.LEVEL_1DAY

                kw['level'] = level

                r = recorder_class(**kw)
                r.run()
                return
            else:
                r = recorder_class(**kw)
                r.run()
                return
        else:
            print(f'no recorders for {cls.__name__}')


class NormalMixin(Mixin):
    # the record created time in db
    created_timestamp = Column(DateTime, default=pd.Timestamp.now())
    # the record updated time in db, some recorder would check it for whether need to refresh
    updated_timestamp = Column(DateTime)


class EntityMixin(Mixin):
    entity_type = Column(String(length=64))
    exchange = Column(String(length=32))
    code = Column(String(length=64))
    name = Column(String(length=128))

    @classmethod
    def get_trading_dates(cls, start_date=None, end_date=None):
        """
        overwrite it to get the trading dates of the entity

        :param start_date:
        :param end_date:
        :return:
        """
        return pd.date_range(start_date, end_date, freq='B')

    @classmethod
    def get_trading_intervals(cls):
        """
        overwrite it to get the trading intervals of the entity

        :return:[(start,end)]
        """
        return [('09:30', '11:30'), ('13:00', '15:00')]

    @classmethod
    def get_interval_timestamps(cls, start_date, end_date, level: IntervalLevel):
        """
        generate the timestamps for the level

        :param start_date:
        :param end_date:
        :param level:
        """

        for current_date in cls.get_trading_dates(start_date=start_date, end_date=end_date):
            if level >= IntervalLevel.LEVEL_1DAY:
                yield current_date
            else:
                start_end_list = cls.get_trading_intervals()

                for start_end in start_end_list:
                    start = start_end[0]
                    end = start_end[1]

                    current_timestamp = date_and_time(the_date=current_date, the_time=start)
                    end_timestamp = date_and_time(the_date=current_date, the_time=end)

                    while current_timestamp <= end_timestamp:
                        yield current_timestamp
                        current_timestamp = current_timestamp + timedelta(minutes=level.to_minute())

    @classmethod
    def is_open_timestamp(cls, timestamp):
        timestamp = pd.Timestamp(timestamp)
        return is_same_time(timestamp, date_and_time(the_date=timestamp.date(),
                                                     the_time=cls.get_trading_intervals()[0][0]))

    @classmethod
    def is_close_timestamp(cls, timestamp):
        timestamp = pd.Timestamp(timestamp)
        return is_same_time(timestamp, date_and_time(the_date=timestamp.date(),
                                                     the_time=cls.get_trading_intervals()[-1][1]))

    @classmethod
    def is_finished_kdata_timestamp(cls, timestamp: pd.Timestamp, level: IntervalLevel):
        """
        :param timestamp: the timestamp could be recorded in kdata of the level
        :type timestamp: pd.Timestamp
        :param level:
        :type level: zvt.domain.common.IntervalLevel
        :return:
        :rtype: bool
        """
        timestamp = pd.Timestamp(timestamp)

        for t in cls.get_interval_timestamps(timestamp.date(), timestamp.date(), level=level):
            if is_same_time(t, timestamp):
                return True

        return False

    @classmethod
    def could_short(cls):
        """
        whether could be shorted

        :return:
        """
        return False

    @classmethod
    def get_trading_t(cls):
        """
        0 means t+0
        1 means t+1

        :return:
        """
        return 1


class NormalEntityMixin(EntityMixin):
    # the record created time in db
    created_timestamp = Column(DateTime, default=pd.Timestamp.now())
    # the record updated time in db, some recorder would check it for whether need to refresh
    updated_timestamp = Column(DateTime)
