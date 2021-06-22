# -*- coding: utf-8 -*-
import logging

import requests

from zvt.contract import ActorType

logger = logging.getLogger(__name__)


def get_ii_holder_report_dates(code):
    return get_em_data(request_type='RPT_F10_MAIN_ORGHOLD', fields='REPORT_DATE,IS_COMPLETE',
                       filters=generate_filters(code=code))


def get_ii_holder(code, report_date, org_type):
    return get_em_data(request_type='RPT_MAIN_ORGHOLDDETAIL',
                       fields='SECURITY_CODE,REPORT_DATE,HOLDER_CODE,HOLDER_NAME,TOTAL_SHARES,HOLD_VALUE,FREESHARES_RATIO,ORG_TYPE,SECUCODE,FUND_DERIVECODE',
                       filters=generate_filters(code=code, report_date=report_date, org_type=org_type))


def get_url(type, sty, filters, pn=1, ps=2000):
    return f'https://datacenter.eastmoney.com/securities/api/data/get?type={type}&sty={sty}&filter={filters}&client=APP&source=SECURITIES&p={pn}&ps={ps}&sr=-1&st=&v=01358221180934358'


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


def generate_filters(code=None, report_date=None, org_type=None):
    result = ''
    if code:
        result += f'(SECUCODE="{code}.{get_exchange(code)}")'
    if report_date:
        result += f'(REPORT_DATE=\'{report_date}\')'
    if org_type:
        result += f'(ORG_TYPE="{org_type}")'

    return result


def get_em_data(request_type, fields, filters, pn=1, ps=2000):
    url = get_url(type=request_type, sty=fields, filters=filters, pn=pn, ps=ps)
    resp = requests.get(url)
    if resp.status_code == 200:
        json_result = resp.json()
        if json_result and json_result['result']:
            data: list = json_result['result']['data']
            if json_result['result']['pages'] > pn:
                next_data = get_em_data(request_type=request_type, fields=fields, filters=filters, pn=pn + 1, ps=ps)
                if next_data:
                    data = data + next_data
                    return data
            else:
                return data
        return None
    raise RuntimeError(f'request em data code: {resp.status_code}, error: {resp.text}')


if __name__ == '__main__':
    print(get_ii_holder_report_dates(code='000338'))

    # resp = get_ii_holder(code='000338', report_date='2021-03-31',
    #                      org_type=actor_type_to_org_type(ActorType.corporation))
    # print(resp)
