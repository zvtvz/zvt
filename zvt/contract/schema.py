# -*- coding: utf-8 -*-
import inspect
from datetime import timedelta
from typing import List, Union

import pandas as pd
from sqlalchemy import Column, String, DateTime, Float
from sqlalchemy.orm import Session

from zvt.contract import IntervalLevel
from zvt.utils.time_utils import date_and_time, is_same_time, now_pd_timestamp


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
        # don't make provider_map_recorder as class field,it should be created for the sub class as need
        if not hasattr(cls, 'provider_map_recorder'):
            cls.provider_map_recorder = {}

        if provider not in cls.provider_map_recorder:
            cls.provider_map_recorder[provider] = recorder_cls

    @classmethod
    def register_provider(cls, provider):
        # don't make providers as class field,it should be created for the sub class as need
        if not hasattr(cls, 'providers'):
            cls.providers = []

        if provider not in cls.providers:
            cls.providers.append(provider)

    @classmethod
    def test_data_correctness(cls, provider, data_samples):
        for data in data_samples:
            item = cls.query_data(provider=provider, ids=[data['id']], return_type='dict')
            print(item)
            for k in data:
                if k == 'timestamp':
                    assert is_same_time(item[0][k], data[k])
                else:
                    assert item[0][k] == data[k]

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
                    one_day_trading_minutes=None,
                    **kwargs):
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

                # add other custom args
                for k in kwargs:
                    kw[k] = kwargs[k]

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


class Player(Mixin):
    # 参与者类型
    player_type = Column(String(length=64))
    # 所属国家
    country = Column(String(length=32))
    # 编码
    code = Column(String(length=64))
    # 名字
    name = Column(String(length=128))


class EntityMixin(Mixin):
    # 标的类型
    entity_type = Column(String(length=64))
    # 所属交易所
    exchange = Column(String(length=32))
    # 编码
    code = Column(String(length=64))
    # 名字
    name = Column(String(length=128))
    # 上市日
    list_date = Column(DateTime)
    # 退市日
    end_date = Column(DateTime)

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
            if level == IntervalLevel.LEVEL_1DAY:
                yield current_date
            elif level == IntervalLevel.LEVEL_1WEEK:
                if current_date.weekday() == 4:
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


class Portfolio(EntityMixin):
    @classmethod
    def get_stocks(cls,
                   code=None, codes=None, ids=None, timestamp=now_pd_timestamp(), provider=None):
        """
        the publishing policy of portfolio positions is different for different types,
        overwrite this function for get the holding stocks in specific date

        :param code: portfolio(etf/block/index...) code
        :param codes: portfolio(etf/block/index...) codes
        :param ids: portfolio(etf/block/index...) ids
        :param timestamp: the date of the holding stocks
        :param provider: the data provider
        :return:
        """
        from zvt.contract.api import get_schema_by_name
        schema_str = f'{cls.__name__}Stock'
        portfolio_stock = get_schema_by_name(schema_str)
        return portfolio_stock.query_data(provider=provider, code=code, codes=codes, timestamp=timestamp, ids=ids)


# 组合(Fund,Etf,Index,Block等)和个股(Stock)的关系 应该继承自该类
# 该基础类可以这样理解:
# entity为组合本身,其包含了stock这种entity,timestamp为持仓日期,从py的"你知道你在干啥"的哲学出发，不加任何约束
class PortfolioStock(Mixin):
    # portfolio标的类型
    entity_type = Column(String(length=64))
    # portfolio所属交易所
    exchange = Column(String(length=32))
    # portfolio编码
    code = Column(String(length=64))
    # portfolio名字
    name = Column(String(length=128))

    stock_id = Column(String)
    stock_code = Column(String(length=64))
    stock_name = Column(String(length=128))


# 支持时间变化,报告期标的调整
class PortfolioStockHistory(PortfolioStock):
    # 报告期,season1,half_year,season3,year
    report_period = Column(String(length=32))
    # 3-31,6-30,9-30,12-31
    report_date = Column(DateTime)

    # 占净值比例
    proportion = Column(Float)
    # 持有股票的数量
    shares = Column(Float)
    # 持有股票的市值
    market_cap = Column(Float)


__all__ = ['EntityMixin', 'Mixin', 'NormalMixin', 'NormalEntityMixin', 'Portfolio', 'PortfolioStock',
           'PortfolioStockHistory']
