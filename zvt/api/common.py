# -*- coding: utf-8 -*-

import math
from typing import Union

import pandas as pd
from sqlalchemy import exists, and_, func
from sqlalchemy.orm import Query

from zvt.domain import SecurityType, Stock, Index, ReportPeriod, StoreCategory, \
    StockIndex
from zvt.domain import get_db_session, CompanyType, TradingLevel, get_store_category
from zvt.domain.coin_meta import Coin
from zvt.domain.quote import *
from zvt.utils.pd_utils import index_df, df_is_not_null
from zvt.utils.time_utils import to_pd_timestamp, now_pd_timestamp
from zvt.utils.time_utils import to_time_str, TIME_FORMAT_DAY, TIME_FORMAT_ISO8601


def get_security_schema(security_type: Union[SecurityType, str]):
    if SecurityType(security_type) == SecurityType.stock:
        return Stock
    if SecurityType(security_type) == SecurityType.index:
        return Index
    if SecurityType(security_type) == SecurityType.coin:
        return Coin


def get_kdata_schema(security_type: Union[SecurityType, str],
                     level: Union[TradingLevel, str] = TradingLevel.LEVEL_1DAY):
    if type(level) == str:
        level = TradingLevel(level)
    if type(security_type) == str:
        security_type = SecurityType(security_type)

    # kdata schema rule
    # 1)name:{SecurityType.value.capitalize()}{TradingLevel.value.upper()}Kdata
    if level == TradingLevel.LEVEL_TICK:
        schema_str = '{}{}Kdata'.format(security_type.value.capitalize(), level.value.capitalize())
    else:
        schema_str = '{}{}Kdata'.format(security_type.value.capitalize(), level.value.upper())

    return eval(schema_str)


def to_report_period_type(report_period):
    the_date = to_pd_timestamp(report_period)
    if the_date.month == 3 and the_date.day == 31:
        return ReportPeriod.season1
    if the_date.month == 6 and the_date.day == 30:
        return ReportPeriod.half_year
    if the_date.month == 9 and the_date.day == 30:
        return ReportPeriod.season3
    if the_date.month == 12 and the_date.day == 31:
        return ReportPeriod.year

    return None


def get_report_period(the_date=now_pd_timestamp()):
    if the_date.month >= 10:
        return "{}{}".format(the_date.year, '-09-30')
    elif the_date.month >= 7:
        return "{}{}".format(the_date.year, '-06-30')
    elif the_date.month >= 4:
        return "{}{}".format(the_date.year, '-03-31')
    else:
        return "{}{}".format(the_date.year - 1, '-12-31')


def next_report_period(start_report_period, size=10):
    year = start_report_period.year + math.floor(size / 4)
    month = start_report_period.month
    day = start_report_period.day

    t = pd.Timestamp(year=year, month=month, day=day) + pd.Timedelta(days=(size % 4) * 31)
    return get_report_period(t)


def common_filter(query: Query, data_schema, start_timestamp=None, end_timestamp=None,
                  filters=None, order=None, limit=None):
    if start_timestamp:
        query = query.filter(data_schema.timestamp >= to_pd_timestamp(start_timestamp))
    if end_timestamp:
        query = query.filter(data_schema.timestamp <= to_pd_timestamp(end_timestamp))

    if filters:
        for filter in filters:
            query = query.filter(filter)
    if order is not None:
        query = query.order_by(order)
    else:
        query = query.order_by(data_schema.timestamp.asc())
    if limit:
        query = query.limit(limit)

    return query


def get_count(data_schema, filters=None, session=None):
    query = session.query(data_schema)
    if filters:
        for filter in filters:
            query = query.filter(filter)

    count_q = query.statement.with_only_columns([func.count()]).order_by(None)
    count = session.execute(count_q).scalar()
    return count


def get_group(provider, data_schema, column, group_func=func.count, session=None):
    local_session = False
    if not session:
        store_category = get_store_category(data_schema)
        session = get_db_session(provider=provider, store_category=store_category)
        local_session = True
    try:
        if group_func:
            query = session.query(column, group_func(column)).group_by(column)
        else:
            query = session.query(column).group_by(column)
        df = pd.read_sql(query.statement, query.session.bind)
        return df
    except Exception:
        raise
    finally:
        if local_session:
            session.close()


def get_data(data_schema, security_list=None, security_id=None, codes=None, level=None, provider='eastmoney',
             columns=None, return_type='df', start_timestamp=None, end_timestamp=None,
             filters=None, session=None, order=None, limit=None, index='timestamp', index_is_time=True):
    local_session = False
    if not session:
        store_category = get_store_category(data_schema)
        session = get_db_session(provider=provider, store_category=store_category)
        local_session = True

    try:
        if columns:
            if data_schema.timestamp not in columns:
                columns.append(data_schema.timestamp)
            query = session.query(*columns)
        else:
            query = session.query(data_schema)

        if security_id:
            query = query.filter(data_schema.security_id == security_id)
        if codes:
            query = query.filter(data_schema.code.in_(codes))
        if security_list:
            query = query.filter(data_schema.security_id.in_(security_list))

        # we always store different level in different schema,the level param is not useful now
        if level:
            try:
                # some schema has no level,just ignore it
                data_schema.level
                if type(level) == TradingLevel:
                    level = level.value
                query = query.filter(data_schema.level == level)
            except Exception as e:
                pass

        query = common_filter(query, data_schema=data_schema, start_timestamp=start_timestamp,
                              end_timestamp=end_timestamp, filters=filters, order=order, limit=limit)

        if return_type == 'df':
            df = pd.read_sql(query.statement, query.session.bind)
            if df_is_not_null(df):
                return index_df(df, drop=False, index=index, index_is_time=index_is_time)
        elif return_type == 'domain':
            return query.all()
        elif return_type == 'dict':
            return [item.__dict__ for item in query.all()]
    except Exception:
        raise
    finally:
        if local_session:
            session.close()


def get_stock_category(stock_id, session=None):
    local_session = False
    if not session:
        session = get_db_session(store_category=StoreCategory.meta)
        local_session = True
    try:
        return session.query(Index).filter(Index.stocks.any(id=stock_id)).all()
    except Exception:
        raise
    finally:
        if local_session:
            session.close()


def get_company_type(stock_domain: Stock):
    industries = stock_domain.industries.split(',')
    if ('银行' in industries) or ('信托' in industries):
        return CompanyType.yinhang
    if '保险' in industries:
        return CompanyType.baoxian
    if '证券' in industries:
        return CompanyType.quanshang
    return CompanyType.qiye


def data_exist(session, schema, id):
    return session.query(exists().where(and_(schema.id == id))).scalar()


def decode_security_id(security_id: str):
    result = security_id.split('_')
    security_type = result[0]
    exchange = result[1]
    code = result[2]
    return SecurityType(security_type), exchange, code


def get_exchange(code):
    if code >= '333333':
        return 'sh'
    else:
        return 'sz'


def china_stock_code_to_id(code):
    return "{}_{}_{}".format('stock', get_exchange(code), code)


def get_one_day_trading_minutes(security_id: str = None, security_type: SecurityType = None):
    if security_type is None:
        security_type, _, _ = decode_security_id(security_id)
    if security_type == SecurityType.coin:
        return 24 * 60
    if security_type == SecurityType.stock:
        return 4 * 60


def get_close_time(security_id: str):
    """

    :param security_id:
    :type security_id: str
    :return:0,0 means never stop
    :rtype: Tuple[int, int]
    """
    security_type, _, _ = decode_security_id(security_id)
    if security_type == SecurityType.coin:
        return 0, 0
    if security_type == SecurityType.stock:
        return 15, 0


def is_close_time(security_id, the_timestamp):
    close_hour, close_minute = get_close_time(security_id)

    return the_timestamp.hour == close_hour and the_timestamp.minute == close_minute


def get_open_time(security_id: str):
    security_type, _, _ = decode_security_id(security_id)
    if security_type == SecurityType.coin:
        return 0, 0
    if security_type == SecurityType.stock:
        return 9, 30


def generate_kdata_id(security_id, timestamp, level):
    if level == TradingLevel.LEVEL_1DAY:
        return "{}_{}".format(security_id, to_time_str(timestamp, fmt=TIME_FORMAT_DAY))
    else:
        return "{}_{}".format(security_id, to_time_str(timestamp, fmt=TIME_FORMAT_ISO8601))


def security_id_in_index(security_id, index_id, session=None, data_schema=StockIndex, provider='eastmoney'):
    the_id = '{}_{}'.format(index_id, security_id)
    local_session = False
    if not session:
        store_category = get_store_category(data_schema)
        session = get_db_session(provider=provider, store_category=store_category)
        local_session = True

    try:
        return data_exist(session=session, schema=data_schema, id=the_id)
    except Exception:
        raise
    finally:
        if local_session:
            session.close()


# joinquant related transform
def to_jq_security_id(security_item):
    if security_item.type == SecurityType.stock.value:
        if security_item.exchange == 'sh':
            return '{}.XSHG'.format(security_item.code)
        if security_item.exchange == 'sz':
            return '{}.XSHE'.format(security_item.code)


def to_jq_trading_level(trading_level: TradingLevel):
    if trading_level < TradingLevel.LEVEL_1HOUR:
        return trading_level.value

    if trading_level == TradingLevel.LEVEL_1HOUR:
        return '60m'
    if trading_level == TradingLevel.LEVEL_1DAY:
        return '1d'


def to_jq_report_period(timestamp):
    the_date = to_pd_timestamp(timestamp)
    report_period = to_report_period_type(timestamp)
    if report_period == ReportPeriod.year:
        return '{}'.format(the_date.year)
    if report_period == ReportPeriod.season1:
        return '{}q1'.format(the_date.year)
    if report_period == ReportPeriod.half_year:
        return '{}q2'.format(the_date.year)
    if report_period == ReportPeriod.season3:
        return '{}q3'.format(the_date.year)


# ccxt related transform
def to_ccxt_trading_level(trading_level: TradingLevel):
    return trading_level.value


if __name__ == '__main__':
    assert get_kdata_schema(security_type='stock', level=TradingLevel.LEVEL_1DAY) == Stock1DKdata
    assert get_kdata_schema(security_type='stock', level=TradingLevel.LEVEL_15MIN) == Stock15MKdata
    assert get_kdata_schema(security_type='stock', level=TradingLevel.LEVEL_1HOUR) == Stock1HKdata

    assert get_kdata_schema(security_type='coin', level=TradingLevel.LEVEL_1DAY) == Coin1DKdata
    assert get_kdata_schema(security_type='coin', level=TradingLevel.LEVEL_1MIN) == Coin1MKdata
