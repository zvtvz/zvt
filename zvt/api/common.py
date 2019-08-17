# -*- coding: utf-8 -*-

import math
from typing import Union

import pandas as pd
from sqlalchemy import exists, and_

from zvdata.api import decode_entity_id
from zvdata.domain import get_db_session
from zvdata.structs import IntervalLevel
from zvt.domain import ReportPeriod, CompanyType
from zvt.domain.quote import *
from zvt.domain.stock_meta import Index, Stock, StockIndex
from zvt.utils.time_utils import to_pd_timestamp, now_pd_timestamp
from zvt.utils.time_utils import to_time_str, TIME_FORMAT_DAY, TIME_FORMAT_ISO8601


def has_report_period(schema_name):
    if schema_name in ['BalanceSheet', 'IncomeStatement', 'CashFlowStatement', 'FinanceFactor']:
        return True
    return False


def get_important_column(schema_name):
    if schema_name == 'FinanceFactor':
        return ['basic_eps', 'total_op_income', 'net_profit', 'op_income_growth_yoy', 'net_profit_growth_yoy', 'roe',
                'rota', 'gross_profit_margin', 'net_margin']

    if schema_name == 'BalanceSheet':
        return ['total_assets', 'total_liabilities', 'equity', 'cash_and_cash_equivalents', 'accounts_receivable',
                'inventories', 'goodwill']

    if schema_name == 'IncomeStatement':
        return ['operating_income', 'investment_income', 'total_operating_costs', 'total_profits', 'sales_costs',
                'managing_costs', 'financing_costs']

    if schema_name == 'CashFlowStatement':
        return ['net_op_cash_flows', 'net_investing_cash_flows', 'net_financing_cash_flows', 'cash']

    return []


def get_kdata_schema(entity_type: str,
                     level: Union[IntervalLevel, str] = IntervalLevel.LEVEL_1DAY):
    if type(level) == str:
        level = IntervalLevel(level)

    # kdata schema rule
    # 1)name:{SecurityType.value.capitalize()}{IntervalLevel.value.upper()}Kdata
    schema_str = '{}{}Kdata'.format(entity_type.capitalize(), level.value.capitalize())

    return eval(schema_str)


def to_report_period_type(report_period):
    the_date = to_pd_timestamp(report_period)
    if the_date.month == 3 and the_date.day == 31:
        return ReportPeriod.season1.value
    if the_date.month == 6 and the_date.day == 30:
        return ReportPeriod.half_year.value
    if the_date.month == 9 and the_date.day == 30:
        return ReportPeriod.season3.value
    if the_date.month == 12 and the_date.day == 31:
        return ReportPeriod.year.value

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


def get_stock_category(stock_id, session=None):
    local_session = False
    if not session:
        session = get_db_session(db_name='meta')
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


def get_exchange(code):
    if code >= '333333':
        return 'sh'
    else:
        return 'sz'


def china_stock_code_to_id(code):
    return "{}_{}_{}".format('stock', get_exchange(code), code)


def get_one_day_trading_minutes(entity_id: str = None, entity_type: str = None):
    if entity_type is None:
        entity_type, _, _ = decode_entity_id(entity_id)
    if entity_type == 'coin':
        return 24 * 60
    if entity_type == 'stock':
        return 4 * 60


def get_close_time(entity_id: str):
    """

    :param entity_id:
    :type entity_id: str
    :return:0,0 means never stop
    :rtype: Tuple[int, int]
    """
    entity_type, _, _ = decode_entity_id(entity_id)
    if entity_type == 'coin':
        return 0, 0
    if entity_type == 'stock':
        return 15, 0


def is_close_time(entity_id, the_timestamp):
    close_hour, close_minute = get_close_time(entity_id)

    return the_timestamp.hour == close_hour and the_timestamp.minute == close_minute


def get_open_time(entity_id: str):
    entity_type, _, _ = decode_entity_id(entity_id)
    if entity_type == 'coin':
        return 0, 0
    if entity_type == 'stock':
        return 9, 30


def generate_kdata_id(entity_id, timestamp, level):
    if level == IntervalLevel.LEVEL_1DAY:
        return "{}_{}".format(entity_id, to_time_str(timestamp, fmt=TIME_FORMAT_DAY))
    else:
        return "{}_{}".format(entity_id, to_time_str(timestamp, fmt=TIME_FORMAT_ISO8601))


def stock_id_in_index(stock_id, index_id, session=None, data_schema=StockIndex, provider='eastmoney'):
    the_id = '{}_{}'.format(index_id, stock_id)
    local_session = False
    if not session:
        session = get_db_session(provider=provider, data_schema=data_schema)
        local_session = True

    try:
        return data_exist(session=session, schema=data_schema, id=the_id)
    except Exception:
        raise
    finally:
        if local_session:
            session.close()


# joinquant related transform
def to_jq_entity_id(security_item):
    if security_item.entity_type == 'stock':
        if security_item.exchange == 'sh':
            return '{}.XSHG'.format(security_item.code)
        if security_item.exchange == 'sz':
            return '{}.XSHE'.format(security_item.code)


def to_jq_trading_level(trading_level: IntervalLevel):
    if trading_level < IntervalLevel.LEVEL_1HOUR:
        return trading_level.value

    if trading_level == IntervalLevel.LEVEL_1HOUR:
        return '60m'
    if trading_level == IntervalLevel.LEVEL_1DAY:
        return '1d'


def to_jq_report_period(timestamp):
    the_date = to_pd_timestamp(timestamp)
    report_period = to_report_period_type(timestamp)
    if report_period == ReportPeriod.year.value:
        return '{}'.format(the_date.year)
    if report_period == ReportPeriod.season1.value:
        return '{}q1'.format(the_date.year)
    if report_period == ReportPeriod.half_year.value:
        return '{}q2'.format(the_date.year)
    if report_period == ReportPeriod.season3.value:
        return '{}q3'.format(the_date.year)

    assert False


# ccxt related transform
def to_ccxt_trading_level(trading_level: IntervalLevel):
    return trading_level.value


if __name__ == '__main__':
    assert get_kdata_schema(entity_type='stock', level=IntervalLevel.LEVEL_1DAY) == Stock1dKdata
    assert get_kdata_schema(entity_type='stock', level=IntervalLevel.LEVEL_15MIN) == Stock15mKdata
    assert get_kdata_schema(entity_type='stock', level=IntervalLevel.LEVEL_1HOUR) == Stock1hKdata

    assert get_kdata_schema(entity_type='coin', level=IntervalLevel.LEVEL_1DAY) == Coin1dKdata
    assert get_kdata_schema(entity_type='coin', level=IntervalLevel.LEVEL_1MIN) == Coin1mKdata
