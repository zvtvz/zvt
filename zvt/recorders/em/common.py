# -*- coding: utf-8 -*-
import logging
import random

import requests

from zvt.contract import ActorType

logger = logging.getLogger(__name__)


# 机构持仓日期
def get_ii_holder_report_dates(code):
    return get_em_data(request_type='RPT_F10_MAIN_ORGHOLD', fields='REPORT_DATE,IS_COMPLETE',
                       filters=generate_filters(code=code), sort_by='REPORT_DATE', sort='desc')


# 十大股东持仓日期
def get_holder_report_dates(code):
    return get_em_data(request_type='RPT_F10_EH_HOLDERSDATE', fields='END_DATE,IS_DEFAULT,IS_REPORTDATE',
                       filters=generate_filters(code=code), sort_by='END_DATE', sort='desc')


# 十大流通股东日期
def get_free_holder_report_dates(code):
    return get_em_data(request_type='RPT_F10_EH_FREEHOLDERSDATE', fields='END_DATE,IS_DEFAULT,IS_REPORTDATE',
                       filters=generate_filters(code=code), sort_by='END_DATE', sort='desc')


# 机构持仓
def get_ii_holder(code, report_date, org_type):
    return get_em_data(request_type='RPT_MAIN_ORGHOLDDETAIL',
                       fields='SECURITY_CODE,REPORT_DATE,HOLDER_CODE,HOLDER_NAME,TOTAL_SHARES,HOLD_VALUE,FREESHARES_RATIO,ORG_TYPE,SECUCODE,FUND_DERIVECODE',
                       filters=generate_filters(code=code, report_date=report_date, org_type=org_type))


# 机构持仓汇总
def get_ii_summary(code, report_date, org_type):
    return get_em_data(request_type='RPT_F10_MAIN_ORGHOLDDETAILS',
                       fields='SECURITY_CODE,SECUCODE,REPORT_DATE,ORG_TYPE,TOTAL_ORG_NUM,TOTAL_FREE_SHARES,TOTAL_MARKET_CAP,TOTAL_SHARES_RATIO,CHANGE_RATIO,IS_COMPLETE',
                       filters=generate_filters(code=code, report_date=report_date, org_type=org_type))


def get_free_holders(code, end_date):
    return get_em_data(request_type='RPT_F10_EH_FREEHOLDERS',
                       fields='SECUCODE,END_DATE,HOLDER_NAME,HOLDER_CODE,HOLDER_CODE_OLD,HOLD_NUM,FREE_HOLDNUM_RATIO,FREE_RATIO_QOQ,IS_HOLDORG,HOLDER_RANK',
                       filters=generate_filters(code=code, end_date=end_date), sort_by='HOLDER_RANK')


def get_holders(code, end_date):
    return get_em_data(request_type='RPT_F10_EH_HOLDERS',
                       fields='SECUCODE,END_DATE,HOLDER_NAME,HOLDER_CODE,HOLDER_CODE_OLD,HOLD_NUM,HOLD_NUM_RATIO,HOLD_RATIO_QOQ,HOLDER_RANK,IS_HOLDORG',
                       filters=generate_filters(code=code, end_date=end_date), sort_by='HOLDER_RANK')


def get_url(type, sty, filters, order_by='', order='asc', pn=1, ps=2000):
    # 根据 url 映射如下
    # type=RPT_F10_MAIN_ORGHOLDDETAILS
    # sty=SECURITY_CODE,SECUCODE,REPORT_DATE,ORG_TYPE,TOTAL_ORG_NUM,TOTAL_FREE_SHARES,TOTAL_MARKET_CAP,TOTAL_SHARES_RATIO,CHANGE_RATIO,IS_COMPLETE
    # filter=(SECUCODE="000338.SZ")(REPORT_DATE=\'2021-03-31\')(ORG_TYPE="01")
    # sr=1
    # st=
    if order == 'asc':
        sr = 1
    else:
        sr = -1
    v = random.randint(1000000000000000, 9000000000000000)
    return f'https://datacenter.eastmoney.com/securities/api/data/get?type={type}&sty={sty}&filter={filters}&client=APP&source=SECURITIES&p={pn}&ps={ps}&sr={sr}&st={order_by}&v=0{v}'


def get_exchange(code):
    if code >= '333333':
        return 'SH'
    else:
        return 'SZ'


def actor_type_to_org_type(actor_type: ActorType):
    if actor_type == ActorType.raised_fund:
        return '01'
    if actor_type == ActorType.qfii:
        return '02'
    if actor_type == ActorType.social_security:
        return '03'
    if actor_type == ActorType.broker:
        return '04'
    if actor_type == ActorType.insurance:
        return '05'
    if actor_type == ActorType.trust:
        return '06'
    if actor_type == ActorType.corporation:
        return '07'
    assert False


def generate_filters(code=None, report_date=None, end_date=None, org_type=None):
    result = ''
    if code:
        result += f'(SECUCODE="{code}.{get_exchange(code)}")'
    if report_date:
        result += f'(REPORT_DATE=\'{report_date}\')'
    if org_type:
        result += f'(ORG_TYPE="{org_type}")'
    if end_date:
        result += f'(END_DATE=\'{end_date}\')'

    return result


def get_em_data(request_type, fields, filters, sort_by='', sort='asc', pn=1, ps=2000):
    url = get_url(type=request_type, sty=fields, filters=filters, order_by=sort_by, pn=pn, ps=ps)
    resp = requests.get(url)
    if resp.status_code == 200:
        json_result = resp.json()
        if json_result and json_result['result']:
            data: list = json_result['result']['data']
            if json_result['result']['pages'] > pn:
                next_data = get_em_data(request_type=request_type, fields=fields, filters=filters, sort_by=sort_by,
                                        sort=sort, pn=pn + 1, ps=ps)
                if next_data:
                    data = data + next_data
                    return data
            else:
                return data
        return None
    raise RuntimeError(f'request em data code: {resp.status_code}, error: {resp.text}')


if __name__ == '__main__':
    from pprint import pprint

    # pprint(get_free_holder_report_dates(code='000338'))
    # pprint(get_holder_report_dates(code='000338'))
    # pprint(get_holders(code='000338', end_date='2021-03-31'))
    # pprint(get_free_holders(code='000338', end_date='2021-03-31'))
    # pprint(get_ii_holder(code='000338', report_date='2021-03-31',
    #                      org_type=actor_type_to_org_type(ActorType.corporation)))
    pprint(get_ii_summary(code='000338', report_date='2021-03-31',
                          org_type=actor_type_to_org_type(ActorType.corporation)))
# the __all__ is generated
__all__ = ['get_ii_holder_report_dates', 'get_holder_report_dates', 'get_free_holder_report_dates', 'get_ii_holder', 'get_ii_summary', 'get_free_holders', 'get_holders', 'get_url', 'get_exchange', 'actor_type_to_org_type', 'generate_filters', 'get_em_data']