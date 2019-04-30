# -*- coding: utf-8 -*-

import math

import pandas as pd
from sqlalchemy import exists, and_, func
from sqlalchemy.orm import Query

from zvt.domain import SecurityType, Stock, Index, StockKdata, IndexKdata, ReportPeriod, StoreCategory
from zvt.domain import get_db_session, CompanyType, TradingLevel, StockIndex, get_store_category, \
    StockKdataBase
from zvt.utils.time_utils import to_pd_timestamp, now_pd_timestamp
from zvt.utils.time_utils import to_time_str, TIME_FORMAT_DAY, TIME_FORMAT_ISO8601


def get_security_schema(security_type):
    if SecurityType(security_type) == SecurityType.stock:
        return Stock
    if SecurityType(security_type) == SecurityType.index:
        return Index


def get_kdata_schema(security_type):
    if SecurityType(security_type) == SecurityType.stock:
        return StockKdata
    if SecurityType(security_type) == SecurityType.index:
        return IndexKdata


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
                  filters=None, order=None, limit=None, provider='eastmoney'):
    if start_timestamp:
        query = query.filter(data_schema.timestamp >= to_pd_timestamp(start_timestamp))
    if end_timestamp:
        query = query.filter(data_schema.timestamp <= to_pd_timestamp(end_timestamp))
    if provider:
        query = query.filter(data_schema.provider == provider)

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


def get_count(data_schema, provider='eastmoney',
              filters=None, session=None):
    query = session.query(data_schema)
    query = query.filter(data_schema.provider == provider)
    if filters:
        for filter in filters:
            query = query.filter(filter)

    count_q = query.statement.with_only_columns([func.count()]).order_by(None)
    count = session.execute(count_q).scalar()
    return count


def get_data(data_schema, security_id=None, codes=None, level=None, provider='eastmoney', columns=None,
             return_type='df', start_timestamp=None, end_timestamp=None,
             filters=None, session=None, order=None, limit=None):
    # assert (security_id is None) != (codes is None)

    if isinstance(data_schema, StockKdataBase):
        assert level != None

    local_session = False
    if not session:
        store_category = get_store_category(data_schema)
        session = get_db_session(store_category=store_category)
        local_session = True

    try:
        if columns:
            query = session.query(*columns)
        else:
            query = session.query(data_schema)

        if security_id:
            query = query.filter(data_schema.security_id == security_id)
        if codes:
            query = query.filter(data_schema.code.in_(codes))

        if isinstance(data_schema, StockKdataBase):
            query = query.filter(data_schema.level == level)

        query = common_filter(query, data_schema=data_schema, start_timestamp=start_timestamp,
                              end_timestamp=end_timestamp, filters=filters, order=order, limit=limit, provider=provider)

        if return_type == 'df':
            return pd.read_sql(query.statement, query.session.bind)
        elif return_type == 'domain':
            return query.all()
        elif return_type == 'dict':
            return [item.to_json() for item in query.all()]
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


def stock_index_rel_exist(stock_id, index_id, provider, session):
    return session.query(exists().where(and_(
        StockIndex.provider == provider, StockIndex.stock_id == stock_id, StockIndex.index_id == index_id))).scalar()


def data_exist(session, schema, id, provider):
    return session.query(exists().where(and_(schema.id == id, schema.provider == provider))).scalar()


def save_stock_index_rel(stock_id, index_id, provider, session):
    if not stock_index_rel_exist(stock_id, index_id, provider, session):
        session.add(StockIndex(stock_id=stock_id, index_id=index_id, provider=provider))


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


def get_one_day_trading_minutes(security_id: str):
    security_type, _, _ = decode_security_id(security_id)
    if security_type == SecurityType.coin:
        return 24 * 60
    if security_type == SecurityType.stock:
        return 4 * 60


def get_close_time(security_id: str):
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
        return "{}_{}".format(timestamp, to_time_str(timestamp, fmt=TIME_FORMAT_ISO8601))


if __name__ == '__main__':
    store_category = get_store_category(Stock)
    session = get_db_session(store_category=store_category)

    print(get_count(data_schema=Stock, filters=[Stock.exchange == 'sh'], session=session))
