# -*- coding: utf-8 -*-
from typing import Type

from zvt.contract import Mixin
from zvt.domain import ReportPeriod
from zvt.utils import pd_is_not_null
from zvt.utils.time_utils import to_pd_timestamp, now_pd_timestamp


def to_report_period_type(report_date):
    the_date = to_pd_timestamp(report_date)
    if the_date.month == 3 and the_date.day == 31:
        return ReportPeriod.season1.value
    if the_date.month == 6 and the_date.day == 30:
        return ReportPeriod.half_year.value
    if the_date.month == 9 and the_date.day == 30:
        return ReportPeriod.season3.value
    if the_date.month == 12 and the_date.day == 31:
        return ReportPeriod.year.value

    return None


def get_recent_report_date(the_date=now_pd_timestamp(), step=0):
    the_date = to_pd_timestamp(the_date)
    assert step >= 0
    if the_date.month >= 10:
        recent = "{}{}".format(the_date.year, "-09-30")
    elif the_date.month >= 7:
        recent = "{}{}".format(the_date.year, "-06-30")
    elif the_date.month >= 4:
        recent = "{}{}".format(the_date.year, "-03-31")
    else:
        recent = "{}{}".format(the_date.year - 1, "-12-31")

    if step == 0:
        return recent
    else:
        step = step - 1
        return get_recent_report_date(recent, step)


def get_recent_report_period(the_date=now_pd_timestamp(), step=0):
    return to_report_period_type(get_recent_report_date(the_date, step=step))


def get_china_exchange(code):
    if code >= "333333":
        return "sh"
    else:
        return "sz"


def china_stock_code_to_id(code):
    return "{}_{}_{}".format("stock", get_china_exchange(code), code)


def value_to_pct(value, default=0):
    return value / 100 if value else default


def value_multiply(value, multiplier, default=0):
    return value * multiplier if value else default


def float_to_pct_str(value):
    return f"{round(value * 100, 2)}%"


def get_recent_report(data_schema: Type[Mixin], timestamp, entity_id=None, filters=None, max_step=2):
    i = 0
    while i < max_step:
        report_date = get_recent_report_date(the_date=timestamp, step=i)
        if filters:
            filters = filters + [data_schema.report_date == to_pd_timestamp(report_date)]
        else:
            filters = [data_schema.report_date == to_pd_timestamp(report_date)]
        df = data_schema.query_data(entity_id=entity_id, filters=filters)
        if pd_is_not_null(df):
            return df
        i = i + 1


# the __all__ is generated
__all__ = [
    "to_report_period_type",
    "get_recent_report_date",
    "get_recent_report_period",
    "get_china_exchange",
    "china_stock_code_to_id",
    "value_to_pct",
    "value_multiply",
    "float_to_pct_str",
    "get_recent_report",
]
