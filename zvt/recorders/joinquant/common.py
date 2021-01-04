# -*- coding: utf-8 -*-
from zvt.contract import IntervalLevel
from zvt.domain import ReportPeriod


def to_jq_trading_level(trading_level: IntervalLevel):
    if trading_level < IntervalLevel.LEVEL_1HOUR:
        return trading_level.value

    if trading_level == IntervalLevel.LEVEL_1HOUR:
        return '60m'
    if trading_level == IntervalLevel.LEVEL_4HOUR:
        return '240m'
    if trading_level == IntervalLevel.LEVEL_1DAY:
        return '1d'
    if trading_level == IntervalLevel.LEVEL_1WEEK:
        return '1w'
    if trading_level == IntervalLevel.LEVEL_1MON:
        return '1M'


def to_jq_entity_id(security_item):
    if security_item.entity_type == 'stock' or security_item.entity_type == 'index':
        if security_item.exchange == 'sh':
            return '{}.XSHG'.format(security_item.code)
        if security_item.exchange == 'sz':
            return '{}.XSHE'.format(security_item.code)


def to_entity_id(jq_code: str, entity_type):
    try:
        code, exchange = jq_code.split('.')
        if exchange == 'XSHG':
            exchange = 'sh'
        elif exchange == 'XSHE':
            exchange = 'sz'
    except:
        code = jq_code
        exchange = 'sz'

    return f'{entity_type}_{exchange}_{code}'


def jq_to_report_period(jq_report_type):
    if jq_report_type == '第一季度':
        return ReportPeriod.season1.value
    if jq_report_type == '第二季度':
        return ReportPeriod.season2.value
    if jq_report_type == '第三季度':
        return ReportPeriod.season3.value
    if jq_report_type == '第四季度':
        return ReportPeriod.season4.value
    if jq_report_type == '半年度':
        return ReportPeriod.half_year.value
    if jq_report_type == '年度':
        return ReportPeriod.year.value
    assert False


# the __all__ is generated
__all__ = ['to_jq_trading_level', 'to_jq_entity_id', 'to_entity_id', 'jq_to_report_period']