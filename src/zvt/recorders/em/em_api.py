# -*- coding: utf-8 -*-
import logging
import random
from typing import Union

import demjson3
import pandas as pd
import requests

from zvt.api.kdata import generate_kdata_id
from zvt.api.utils import value_to_pct, china_stock_code_to_id
from zvt.contract import ActorType, AdjustType, IntervalLevel, Exchange, TradableType, get_entity_exchanges
from zvt.contract.api import decode_entity_id
from zvt.domain import BlockCategory
from zvt.recorders.consts import DEFAULT_HEADER
from zvt.utils.time_utils import (
    to_pd_timestamp,
    now_timestamp,
    to_time_str,
    current_date,
)
from zvt.utils.utils import to_float, json_callback_param

logger = logging.getLogger(__name__)


# 获取中美国债收益率
def get_treasury_yield(pn=1, ps=2000, fetch_all=True):
    results = get_em_data(
        request_type="RPTA_WEB_TREASURYYIELD",
        source=None,
        fields="ALL",
        sort_by="SOLAR_DATE",
        sort="desc",
        pn=pn,
        ps=ps,
        fetch_all=fetch_all,
    )
    yields = []
    for item in results:
        date = item["SOLAR_DATE"]
        # 中国
        yields.append(
            {
                "id": f"country_galaxy_CN_{to_time_str(date)}",
                "entity_id": "country_galaxy_CN",
                "timestamp": to_pd_timestamp(date),
                "code": "CN",
                "yield_2": item.get("EMM00588704"),
                "yield_5": item.get("EMM00166462"),
                "yield_10": item.get("EMM00166466"),
                "yield_30": item.get("EMM00166469"),
            }
        )
        yields.append(
            {
                "id": f"country_galaxy_US_{to_time_str(date)}",
                "entity_id": "country_galaxy_US",
                "timestamp": to_pd_timestamp(date),
                "code": "US",
                "yield_2": item.get("EMG00001306"),
                "yield_5": item.get("EMG00001308"),
                "yield_10": item.get("EMG00001310"),
                "yield_30": item.get("EMG00001312"),
            }
        )
    return yields


# 机构持仓日期
def get_ii_holder_report_dates(code):
    return get_em_data(
        request_type="RPT_F10_MAIN_ORGHOLD",
        fields="REPORT_DATE,IS_COMPLETE",
        filters=generate_filters(code=code),
        sort_by="REPORT_DATE",
        sort="desc",
    )


def get_dragon_and_tiger_list(start_date, end_date=None):
    start_date = to_time_str(start_date)
    if not end_date:
        end_date = now_timestamp()
    end_date = to_time_str(end_date)
    return get_em_data(
        request_type="RPT_DAILYBILLBOARD_DETAILS",
        fields="ALL",
        source="DataCenter",
        filters=f"(TRADE_DATE>='{start_date}')(TRADE_DATE<='{end_date}')",
        sort_by="TRADE_DATE,SECURITY_CODE",
        sort="asc,asc",
    )


# 龙虎榜
def get_dragon_and_tiger(code, start_date=None):
    return get_em_data(
        request_type="RPT_OPERATEDEPT_TRADE",
        fields="TRADE_ID,TRADE_DATE,EXPLANATION,SECUCODE,SECURITY_CODE,SECURITY_NAME_ABBR,ACCUM_AMOUNT,CHANGE_RATE,NET_BUY,BUY_BUY_TOTAL,BUY_SELL_TOTAL,BUY_RATIO_TOTAL,SELL_BUY_TOTAL,SELL_SELL_TOTAL,SELL_RATIO_TOTAL,TRADE_DIRECTION,RANK,OPERATEDEPT_NAME,BUY_AMT_REAL,SELL_AMT_REAL,BUY_RATIO,SELL_RATIO,BUY_TOTAL,SELL_TOTAL,BUY_TOTAL_NET,SELL_TOTAL_NET,NET",
        filters=generate_filters(code=code, trade_date=start_date, field_op={"trade_date": ">="}),
        params='(groupField=TRADE_ID)(groupedFields=TRADE_DIRECTION,RANK,OPERATEDEPT_NAME,BUY_AMT_REAL,SELL_AMT_REAL,BUY_RATIO,SELL_RATIO,NET")(groupListName="LIST")',
        sort_by="TRADE_DATE,RANK",
        sort="asc,asc",
    )


# 十大股东持仓日期
def get_holder_report_dates(code):
    return get_em_data(
        request_type="RPT_F10_EH_HOLDERSDATE",
        fields="END_DATE,IS_DEFAULT,IS_REPORTDATE",
        filters=generate_filters(code=code),
        sort_by="END_DATE",
        sort="desc",
    )


# 十大流通股东日期
def get_free_holder_report_dates(code):
    return get_em_data(
        request_type="RPT_F10_EH_FREEHOLDERSDATE",
        fields="END_DATE,IS_DEFAULT,IS_REPORTDATE",
        filters=generate_filters(code=code),
        sort_by="END_DATE",
        sort="desc",
    )


# 机构持仓
def get_ii_holder(code, report_date, org_type):
    return get_em_data(
        request_type="RPT_MAIN_ORGHOLDDETAIL",
        fields="SECURITY_CODE,REPORT_DATE,HOLDER_CODE,HOLDER_NAME,TOTAL_SHARES,HOLD_VALUE,FREESHARES_RATIO,ORG_TYPE,SECUCODE,FUND_DERIVECODE",
        filters=generate_filters(code=code, report_date=report_date, org_type=org_type),
    )


# 机构持仓汇总
def get_ii_summary(code, report_date, org_type):
    return get_em_data(
        request_type="RPT_F10_MAIN_ORGHOLDDETAILS",
        fields="SECURITY_CODE,SECUCODE,REPORT_DATE,ORG_TYPE,TOTAL_ORG_NUM,TOTAL_FREE_SHARES,TOTAL_MARKET_CAP,TOTAL_SHARES_RATIO,CHANGE_RATIO,IS_COMPLETE",
        filters=generate_filters(code=code, report_date=report_date, org_type=org_type),
    )


def get_free_holders(code, end_date):
    return get_em_data(
        request_type="RPT_F10_EH_FREEHOLDERS",
        fields="SECUCODE,END_DATE,HOLDER_NAME,HOLDER_CODE,HOLDER_CODE_OLD,HOLD_NUM,FREE_HOLDNUM_RATIO,FREE_RATIO_QOQ,IS_HOLDORG,HOLDER_RANK",
        filters=generate_filters(code=code, end_date=end_date),
        sort_by="HOLDER_RANK",
    )


def get_controlling_shareholder(code):
    holders = get_em_data(
        request_type="RPT_F10_EH_RELATION",
        fields="SECUCODE,HOLDER_NAME,RELATED_RELATION,HOLD_RATIO",
        filters=generate_filters(code=code),
    )

    if holders:
        control = {}
        for holder in holders:
            if holder["RELATED_RELATION"] == "控股股东":
                control["holder"] = holder["HOLDER_NAME"]
            elif holder["RELATED_RELATION"] == "实际控制人":
                control["parent"] = holder["HOLDER_NAME"]
        return control


def get_holders(code, end_date):
    return get_em_data(
        request_type="RPT_F10_EH_HOLDERS",
        fields="SECUCODE,END_DATE,HOLDER_NAME,HOLDER_CODE,HOLDER_CODE_OLD,HOLD_NUM,HOLD_NUM_RATIO,HOLD_RATIO_QOQ,HOLDER_RANK,IS_HOLDORG",
        filters=generate_filters(code=code, end_date=end_date),
        sort_by="HOLDER_RANK",
    )


def _order_param(order: str):
    if order:
        orders = order.split(",")
        return ",".join(["1" if item == "asc" else "-1" for item in orders])
    return order


def get_url(type, sty, source="SECURITIES", filters=None, order_by="", order="asc", pn=1, ps=2000, params=None):
    # 根据 url 映射如下
    # type=RPT_F10_MAIN_ORGHOLDDETAILS
    # sty=SECURITY_CODE,SECUCODE,REPORT_DATE,ORG_TYPE,TOTAL_ORG_NUM,TOTAL_FREE_SHARES,TOTAL_MARKET_CAP,TOTAL_SHARES_RATIO,CHANGE_RATIO,IS_COMPLETE
    # filter=(SECUCODE="000338.SZ")(REPORT_DATE=\'2021-03-31\')(ORG_TYPE="01")
    # sr=1
    # st=
    sr = _order_param(order=order)
    v = random.randint(1000000000000000, 9000000000000000)

    if filters or source:
        url = f"https://datacenter.eastmoney.com/securities/api/data/get?type={type}&sty={sty}&filter={filters}&client=APP&source={source}&p={pn}&ps={ps}&sr={sr}&st={order_by}&v=0{v}"
    else:
        url = f"https://datacenter.eastmoney.com/api/data/get?type={type}&sty={sty}&st={order_by}&sr={sr}&p={pn}&ps={ps}&_={now_timestamp()}"

    if params:
        url = url + f"&params={params}"

    return url


def get_exchange(code):
    code_ = int(code)
    if 800000 >= code_ >= 600000:
        return "SH"
    elif code_ >= 400000:
        return "BJ"
    else:
        return "SZ"


def actor_type_to_org_type(actor_type: ActorType):
    if actor_type == ActorType.raised_fund:
        return "01"
    if actor_type == ActorType.qfii:
        return "02"
    if actor_type == ActorType.social_security:
        return "03"
    if actor_type == ActorType.broker:
        return "04"
    if actor_type == ActorType.insurance:
        return "05"
    if actor_type == ActorType.trust:
        return "06"
    if actor_type == ActorType.corporation:
        return "07"
    assert False


def generate_filters(code=None, trade_date=None, report_date=None, end_date=None, org_type=None, field_op: dict = None):
    args = [item for item in locals().items() if item[1] and (item[0] not in ("code", "org_type", "field_op"))]

    result = ""
    if code:
        result += f'(SECUCODE="{code}.{get_exchange(code)}")'
    if org_type:
        result += f'(ORG_TYPE="{org_type}")'

    for arg in args:
        field = arg[0]
        value = arg[1]
        if field_op:
            op = field_op.get(field, "=")
        else:
            op = "="
        result += f"({field.upper()}{op}'{value}')"

    return result


def get_em_data(
    request_type,
    fields,
    session=None,
    source="SECURITIES",
    filters=None,
    sort_by="",
    sort="asc",
    pn=1,
    ps=2000,
    fetch_all=True,
    fetch_count=1,
    params=None,
):
    url = get_url(
        type=request_type,
        sty=fields,
        source=source,
        filters=filters,
        order_by=sort_by,
        order=sort,
        pn=pn,
        ps=ps,
        params=params,
    )
    print(f"current url: {url}")
    if session:
        resp = session.get(url)
    else:
        resp = requests.get(url)
    if resp.status_code == 200:
        json_result = resp.json()
        resp.close()

        if json_result:
            if json_result.get("result"):
                data: list = json_result["result"]["data"]
                need_next = pn < json_result["result"]["pages"]
            elif json_result.get("data"):
                data: list = json_result["data"]
                need_next = json_result["hasNext"] == 1
            else:
                data = []
                need_next = False
            if fetch_all or fetch_count - 1 > 0:
                if need_next:
                    next_data = get_em_data(
                        session=session,
                        request_type=request_type,
                        fields=fields,
                        source=source,
                        filters=filters,
                        sort_by=sort_by,
                        sort=sort,
                        pn=pn + 1,
                        ps=ps,
                        fetch_all=fetch_all,
                        fetch_count=fetch_count - 1,
                        params=params,
                    )
                    if next_data:
                        data = data + next_data
                        return data
                    else:
                        return data
                else:
                    return data
            else:
                return data
        return None
    raise RuntimeError(f"request em data code: {resp.status_code}, error: {resp.text}")


def get_quotes():
    {
        # 市场,2 A股, 3 港股
        "f1": 2,
        # 最新价 660/100=6.6
        "f2": 660,
        # 涨幅 2000/10000=20%
        "f3": 2000,
        # 涨跌额 110/100=1.1
        "f4": 110,
        # 总手
        "f5": 112596,
        # 成交额
        "f6": 74313472.2,
        # 换手率 239/10000
        "f8": 239,
        # 市盈率 110
        "f9": 11000,
        # code
        "f12": "300175",
        #
        "f13": 0,
        # name
        "f14": "朗源股份",
        "f18": 550,
        "f19": 80,
        "f30": -215,
        # 买入价
        "f31": 660,
        # 卖出价
        "f32": None,
        "f125": 0,
        "f139": 5,
        "f148": 1,
        "f152": 2,
    }
    {
        "f1": 2,
        "f2": 1515,
        "f3": 1002,
        "f4": 138,
        "f5": 547165,
        "f6": 804705199.0,
        "f8": 241,
        "f9": 1575,
        "f12": "601233",
        "f13": 1,
        "f14": "桐昆股份",
        "f18": 1377,
        "f19": 2,
        "f30": -1281,
        # 买入价
        "f31": 1515,
        # 卖出价
        "f32": None,
        "f125": 0,
        "f139": 2,
        "f148": 577,
        "f152": 2,
    }
    {
        "f1": 2,
        "f2": 611,
        "f3": 338,
        "f4": 20,
        "f5": 478746,
        "f6": 293801314.14,
        "f8": 803,
        "f9": 2067,
        "f12": "000788",
        "f13": 0,
        "f14": "北大医药",
        "f18": 591,
        "f19": 6,
        "f30": -4015,
        "f31": 611,
        "f32": 612,
        "f125": 0,
        "f139": 2,
        "f148": 1,
        "f152": 2,
    }


# quote
# url = 'https://push2his.eastmoney.com/api/qt/stock/kline/get?'
# 日线      klt=101
# 周线      klt=102
# 月线      klt=103
#
# limit    lmt=2000
#
# 结束时间   end=20500000
#
# 复权      fqt 0 不复权 1 前复权 2 后复权
#          iscca
#
# 字段
# f51,f52,f53,f54,f55,
# timestamp,open,close,high,low
# f56,f57,f58,f59,f60,f61,f62,f63,f64
# volume,turnover,震幅,change_pct,change,turnover_rate
# 深圳
# secid=0.399001&klt=101&fqt=1&lmt=66&end=20500000&iscca=1&fields1=f1,f2,f3,f4,f5,f6,f7,f8&fields2=f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61,f62,f63,f64&ut=f057cbcbce2a86e2866ab8877db1d059&forcect=1
# secid=0.399001&klt=102&fqt=1&lmt=66&end=20500000&iscca=1&fields1=f1,f2,f3,f4,f5,f6,f7,f8&fields2=f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61,f62,f63,f64&ut=f057cbcbce2a86e2866ab8877db1d059&forcect=1
# secid=0.000338&klt=101&fqt=1&lmt=66&end=20500000&iscca=1&fields1=f1,f2,f3,f4,f5,f6,f7,f8&fields2=f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61,f62,f63,f64&ut=f057cbcbce2a86e2866ab8877db1d059&forcect=1
#
# 港股
# secid=116.01024&klt=102&fqt=1&lmt=66&end=20500000&iscca=1&fields1=f1,f2,f3,f4,f5,f6,f7,f8&fields2=f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61,f62,f63,f64&ut=f057cbcbce2a86e2866ab8877db1d059&forcect=1
# 美股
# secid=106.BABA&klt=102&fqt=1&lmt=66&end=20500000&iscca=1&fields1=f1,f2,f3,f4,f5,f6,f7,f8&fields2=f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61,f62,f63,f64&ut=f057cbcbce2a86e2866ab8877db1d059&forcect=1
#
# 上海
# secid=1.512660&klt=101&fqt=1&lmt=66&end=20500000&iscca=1&fields1=f1,f2,f3,f4,f5,f6,f7,f8&fields2=f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61,f62,f63,f64&ut=f057cbcbce2a86e2866ab8877db1d059&forcect=1
def get_kdata(entity_id, session=None, level=IntervalLevel.LEVEL_1DAY, adjust_type=AdjustType.qfq, limit=10000):
    entity_type, exchange, code = decode_entity_id(entity_id)
    level = IntervalLevel(level)

    sec_id = to_em_sec_id(entity_id)
    fq_flag = to_em_fq_flag(adjust_type)
    level_flag = to_em_level_flag(level)
    # f131 结算价
    # f133 持仓
    # 目前未获取
    url = f"https://push2his.eastmoney.com/api/qt/stock/kline/get?secid={sec_id}&klt={level_flag}&fqt={fq_flag}&lmt={limit}&end=20500000&iscca=1&fields1=f1,f2,f3,f4,f5,f6,f7,f8&fields2=f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61,f62,f63,f64&ut=f057cbcbce2a86e2866ab8877db1d059&forcect=1"

    if session:
        resp = session.get(url, headers=DEFAULT_HEADER)
    else:
        resp = requests.get(url, headers=DEFAULT_HEADER)
    resp.raise_for_status()
    results = resp.json()
    resp.close()
    data = results["data"]

    kdatas = []

    if data:
        klines = data["klines"]
        name = data["name"]

        for result in klines:
            # "2000-01-28,1005.26,1012.56,1173.12,982.13,3023326,3075552000.00"
            # "2021-08-27,19.39,20.30,20.30,19.25,1688497,3370240912.00,5.48,6.01,1.15,3.98,0,0,0"
            # time,open,close,high,low,volume,turnover
            # "2022-04-13,10708,10664,10790,10638,402712,43124771328,1.43,0.57,60,0.00,4667112399583576064,4690067230254170112,1169270784"
            fields = result.split(",")
            the_timestamp = to_pd_timestamp(fields[0])

            the_id = generate_kdata_id(entity_id=entity_id, timestamp=the_timestamp, level=level)

            open = to_float(fields[1])
            close = to_float(fields[2])
            high = to_float(fields[3])
            low = to_float(fields[4])
            volume = to_float(fields[5])
            turnover = to_float(fields[6])
            # 7 振幅
            change_pct = value_to_pct(to_float(fields[8]))
            # 9 变动
            turnover_rate = value_to_pct(to_float(fields[10]))

            kdatas.append(
                dict(
                    id=the_id,
                    timestamp=the_timestamp,
                    entity_id=entity_id,
                    provider="em",
                    code=code,
                    name=name,
                    level=level.value,
                    open=open,
                    close=close,
                    high=high,
                    low=low,
                    volume=volume,
                    turnover=turnover,
                    turnover_rate=turnover_rate,
                    change_pct=change_pct,
                )
            )
    if kdatas:
        df = pd.DataFrame.from_records(kdatas)
        return df


def get_basic_info(entity_id):
    entity_type, exchange, code = decode_entity_id(entity_id)
    if entity_type == "stock":
        url = "https://emh5.eastmoney.com/api/GongSiGaiKuang/GetJiBenZiLiao"
        result_field = "JiBenZiLiao"
    elif entity_type == "stockus":
        url = "https://emh5.eastmoney.com/api/MeiGu/GaiKuang/GetZhengQuanZiLiao"
        result_field = "ZhengQuanZiLiao"
    elif entity_type == "stockhk":
        url = "https://emh5.eastmoney.com/api/GangGu/GaiKuang/GetZhengQuanZiLiao"
        result_field = "ZhengQuanZiLiao"
    else:
        assert False

    data = {"fc": to_em_fc(entity_id=entity_id), "color": "w"}
    resp = requests.post(url=url, json=data, headers=DEFAULT_HEADER)

    resp.raise_for_status()
    resp.close()

    return resp.json()["Result"][result_field]


def get_future_list():
    # 主连
    url = f"https://futsseapi.eastmoney.com/list/filter/2?fid=sp_all&mktid=0&typeid=0&pageSize=1000&pageIndex=0&callbackName=jQuery34106875017735118845_1649736551642&sort=asc&orderBy=idx&_={now_timestamp()}"
    resp = requests.get(url, headers=DEFAULT_HEADER)
    resp.raise_for_status()
    result = json_callback_param(resp.text)
    resp.close()
    # [['DCE', 'im'], ['SHFE', 'rbm'], ['SHFE', 'hcm'], ['SHFE', 'ssm'], ['CZCE', 'SFM'], ['CZCE', 'SMM'], ['SHFE', 'wrm'], ['SHFE', 'cum'], ['SHFE', 'alm'], ['SHFE', 'znm'], ['SHFE', 'pbm'], ['SHFE', 'nim'], ['SHFE', 'snm'], ['INE', 'bcm'], ['SHFE', 'aum'], ['SHFE', 'agm'], ['DCE', 'am'], ['DCE', 'bm'], ['DCE', 'ym'], ['DCE', 'mm'], ['CZCE', 'RSM'], ['CZCE', 'OIM'], ['CZCE', 'RMM'], ['DCE', 'pm'], ['DCE', 'cm'], ['DCE', 'csm'], ['DCE', 'jdm'], ['CZCE', 'CFM'], ['CZCE', 'CYM'], ['CZCE', 'SRM'], ['CZCE', 'APM'], ['CZCE', 'CJM'], ['CZCE', 'PKM'], ['CZCE', 'PMM'], ['CZCE', 'WHM'], ['DCE', 'rrm'], ['CZCE', 'JRM'], ['CZCE', 'RIM'], ['CZCE', 'LRM'], ['DCE', 'lhm'], ['INE', 'scm'], ['SHFE', 'fum'], ['DCE', 'pgm'], ['INE', 'lum'], ['SHFE', 'bum'], ['CZCE', 'MAM'], ['DCE', 'egm'], ['DCE', 'lm'], ['CZCE', 'TAM'], ['DCE', 'vm'], ['DCE', 'ppm'], ['DCE', 'ebm'], ['CZCE', 'SAM'], ['CZCE', 'FGM'], ['CZCE', 'URM'], ['SHFE', 'rum'], ['INE', 'nrm'], ['SHFE', 'spm'], ['DCE', 'fbm'], ['DCE', 'bbm'], ['CZCE', 'PFM'], ['DCE', 'jmm'], ['DCE', 'jm'], ['CZCE', 'ZCM'], ['8', '060120'], ['8', '040120'], ['8', '070120'], ['8', '110120'], ['8', '050120'], ['8', '130120']]
    futures = []
    for item in result["list"]:
        entity = {}
        entity["exchange"], entity["code"] = item["uid"].split("|")

        # {'8', 'CZCE', 'DCE', 'INE', 'SHFE'}
        if entity["exchange"] == "8":
            entity["exchange"] = "cffex"
            entity["code"] = to_zvt_code(entity["code"])
        else:
            entity["exchange"] = Exchange(entity["exchange"].lower()).value
            if entity["code"][-1].lower() == "m":
                entity["code"] = entity["code"][:-1]
            else:
                assert False
            entity["code"] = entity["code"].upper()

        entity["entity_type"] = "future"
        entity["name"] = item["name"]
        entity["id"] = f"future_{entity['exchange']}_{entity['code']}"
        entity["entity_id"] = entity["id"]
        futures.append(entity)
    df = pd.DataFrame.from_records(data=futures)
    return df


def get_tradable_list(
    entity_type: Union[TradableType, str] = "stock",
    exchange: Union[Exchange, str] = None,
    limit: int = 10000,
    hk_south=False,
    block_category=BlockCategory.concept,
):
    entity_type = TradableType(entity_type)
    if entity_type == TradableType.future:
        return get_future_list()

    exchanges = get_entity_exchanges(entity_type=entity_type)

    if exchange is not None:
        assert exchange in exchanges
        exchanges = [exchange]

    dfs = []
    for exchange in exchanges:
        exchange = Exchange(exchange)
        ex_flag = to_em_entity_flag(exchange=exchange)
        entity_flag = f"fs=m:{ex_flag}"

        if entity_type == TradableType.index:
            if exchange == Exchange.sh:
                entity_flag = "fs=i:1.000001,i:1.000002,i:1.000003,i:1.000009,i:1.000010,i:1.000011,i:1.000012,i:1.000016,i:1.000300,i:1.000903,i:1.000905,i:1.000906,i:1.000688,i:1.000852,i:2.932000"
            if exchange == Exchange.sz:
                entity_flag = "fs=i:0.399001,i:0.399002,i:0.399003,i:0.399004,i:0.399005,i:0.399006,i:0.399100,i:0.399106,i:0.399305,i:0.399550"
        elif entity_type == TradableType.currency:
            entity_flag = "fs=m:119,m:120"
        elif entity_type == TradableType.indexus:
            # 纳斯达克，道琼斯，标普500，美元指数
            entity_flag = "fs=i:100.NDX,i:100.DJIA,i:100.SPX,i:100.UDI"
        elif entity_type == TradableType.cbond:
            if exchange == Exchange.sz:
                entity_flag = "fs=m:0+e:11"
            elif exchange == Exchange.sh:
                entity_flag = "fs=m:1+e:11"
            else:
                assert False
        # m为交易所代码，t为交易类型
        elif entity_type in [TradableType.block, TradableType.stock, TradableType.stockus, TradableType.stockhk]:
            if exchange == Exchange.sh:
                # t=2 主板
                # t=23 科创板
                entity_flag = "fs=m:1+t:2,m:1+t:23"
            if exchange == Exchange.sz:
                # t=6 主板
                # t=80 创业板
                entity_flag = "fs=m:0+t:6,m:0+t:13,m:0+t:80"
            if exchange == Exchange.bj:
                entity_flag = "fs=m:0+t:81+s:2048"
            if exchange == Exchange.hk:
                if hk_south:
                    # 港股通
                    entity_flag = "fs=b:DLMK0144,b:DLMK0146"
                else:
                    # t=3 主板
                    # t=4 创业板
                    entity_flag = f"fs=m:116+t:3,m:116+t:4"
            if exchange == Exchange.nasdaq:
                # t=1
                # t=3 中概股
                entity_flag = f"fs=m:105+t:1,m:105+t:3"
            if exchange == Exchange.nyse:
                # t=1
                # t=3 中概股
                entity_flag = f"fs=m:106+t:1,m:105+t:3"
            if exchange == Exchange.cn:
                if block_category == BlockCategory.industry:
                    entity_flag = entity_flag + "+t:2"
                elif block_category == BlockCategory.concept:
                    entity_flag = entity_flag + "+t:3"
                else:
                    assert False

        fields = "f1,f2,f3,f4,f12,f13,f14"
        if entity_type == TradableType.stock:
            # 市值,流通市值,pe,pb
            fields = fields + ",f20,f21,f9,f23"
        url = f"https://push2.eastmoney.com/api/qt/clist/get?np=1&fltt=2&invt=2&fields={fields}&pn=1&pz={limit}&fid=f3&po=1&{entity_flag}&ut=f057cbcbce2a86e2866ab8877db1d059&forcect=1&cb=cbCallbackMore&&callback=jQuery34109676853980006124_{now_timestamp() - 1}&_={now_timestamp()}"
        resp = requests.get(url, headers=DEFAULT_HEADER)

        resp.raise_for_status()

        result = json_callback_param(resp.text)
        resp.close()
        data = result["data"]["diff"]
        df = pd.DataFrame.from_records(data=data)
        if entity_type == TradableType.stock:
            df = df[["f12", "f13", "f14", "f20", "f21", "f9", "f23"]]
            df.columns = ["code", "exchange", "name", "cap", "cap1", "pe", "pb"]
            df[["cap", "cap1", "pe", "pb"]] = df[["cap", "cap1", "pe", "pb"]].apply(pd.to_numeric, errors="coerce")
        else:
            df = df[["f12", "f13", "f14"]]
            df.columns = ["code", "exchange", "name"]

        df["exchange"] = exchange.value
        df["entity_type"] = entity_type.value
        df["id"] = df[["entity_type", "exchange", "code"]].apply(lambda x: "_".join(x.astype(str)), axis=1)
        df["entity_id"] = df["id"]
        if entity_type == TradableType.block:
            df["category"] = block_category.value

        dfs.append(df)

    return pd.concat(dfs)


def get_block_stocks(block_id, name=""):
    entity_type, exchange, code = decode_entity_id(block_id)
    category_stocks_url = f"http://48.push2.eastmoney.com/api/qt/clist/get?cb=jQuery11240710111145777397_{now_timestamp() - 1}&pn=1&pz=1000&po=1&np=1&ut=bd1d9ddb04089700cf9c27f6f7426281&fltt=2&invt=2&wbp2u=4668014655929990|0|1|0|web&fid=f3&fs=b:{code}+f:!50&fields=f1,f2,f3,f4,f5,f6,f7,f8,f9,f10,f12,f13,f14,f15,f16,f17,f18,f20,f21,f23,f24,f25,f22,f11,f62,f128,f136,f115,f152,f45&_={now_timestamp()}"
    resp = requests.get(category_stocks_url, headers=DEFAULT_HEADER)
    data = json_callback_param(resp.text)["data"]
    the_list = []
    if data:
        results = data["diff"]
        for result in results:
            stock_code = result["f12"]
            stock_name = result["f14"]
            stock_id = china_stock_code_to_id(stock_code)

            the_list.append(
                {
                    "id": "{}_{}".format(block_id, stock_id),
                    "entity_id": block_id,
                    "entity_type": "block",
                    "exchange": exchange,
                    "code": code,
                    "name": name,
                    "timestamp": current_date(),
                    "stock_id": stock_id,
                    "stock_code": stock_code,
                    "stock_name": stock_name,
                }
            )
    return the_list


def get_news(entity_id, ps=200, index=1, start_timestamp=None, session=None, latest_code=None):
    sec_id = to_em_sec_id(entity_id=entity_id)
    url = f"https://np-listapi.eastmoney.com/comm/wap/getListInfo?cb=callback&client=wap&type=1&mTypeAndCode={sec_id}&pageSize={ps}&pageIndex={index}&callback=jQuery1830017478247906740352_{now_timestamp() - 1}&_={now_timestamp()}"
    logger.info(f"get news from: {url}")
    if session:
        resp = session.get(url)
    else:
        resp = requests.get(url)
    # {
    #     "Art_ShowTime": "2022-02-11 14:29:25",
    #     "Art_Image": "",
    #     "Art_MediaName": "每日经济新闻",
    #     "Art_Code": "202202112274017262",
    #     "Art_Title": "潍柴动力：巴拉德和锡里斯不纳入合并财务报表范围",
    #     "Art_SortStart": "1644560965017262",
    #     "Art_VideoCount": 0,
    #     "Art_OriginUrl": "http://finance.eastmoney.com/news/1354,202202112274017262.html",
    #     "Art_Url": "http://finance.eastmoney.com/a/202202112274017262.html",
    # }
    if resp.status_code == 200:
        json_text = resp.text[resp.text.index("(") + 1 : resp.text.rindex(")")]
        if "list" in demjson3.decode(json_text)["data"]:
            json_result = demjson3.decode(json_text)["data"]["list"]
            resp.close()
            if json_result:
                news = [
                    {
                        "id": f'{entity_id}_{item.get("Art_ShowTime", "")}',
                        "entity_id": entity_id,
                        "timestamp": to_pd_timestamp(item.get("Art_ShowTime", "")),
                        "news_code": item.get("Art_Code", ""),
                        "news_url": item.get("Art_Url", ""),
                        "news_title": item.get("Art_Title", ""),
                    }
                    for index, item in enumerate(json_result)
                    if not start_timestamp
                    or (
                        (to_pd_timestamp(item["Art_ShowTime"]) >= start_timestamp)
                        and (item.get("Art_Code", "") != latest_code)
                    )
                ]
                if len(news) < len(json_result):
                    return news
                next_data = get_news(entity_id=entity_id, ps=ps, index=index + 1)
                if next_data:
                    return news + next_data
                else:
                    return news
        else:
            return None

    logger.error(f"request em data code: {resp.status_code}, error: {resp.text}")


# utils to transform zvt entity to em entity
def to_em_fc(entity_id):
    entity_type, exchange, code = decode_entity_id(entity_id)
    if entity_type == "stock":
        if exchange == "sh":
            return f"{code}01"
        if exchange == "sz":
            return f"{code}02"

    if entity_type == "stockhk":
        return code

    if entity_type == "stockus":
        if exchange == "nyse":
            return f"{code}.N"
        if exchange == "nasdaq":
            return f"{code}.O"


exchange_map_em_flag = {
    #: 深证交易所
    Exchange.sz: 0,
    #: 上证交易所
    Exchange.sh: 1,
    #: 北交所
    Exchange.bj: 0,
    #: 纳斯达克
    Exchange.nasdaq: 105,
    #: 纽交所
    Exchange.nyse: 106,
    #: 中国金融期货交易所
    Exchange.cffex: 8,
    #: 上海期货交易所
    Exchange.shfe: 113,
    #: 大连商品交易所
    Exchange.dce: 114,
    #: 郑州商品交易所
    Exchange.czce: 115,
    #: 上海国际能源交易中心
    Exchange.ine: 142,
    #: 港交所
    Exchange.hk: 116,
    #: 中国行业/概念板块
    Exchange.cn: 90,
    #: 美国指数
    Exchange.us: 100,
    #: 汇率
    Exchange.forex: 119,
}


def to_em_entity_flag(exchange: Union[Exchange, str]):
    exchange = Exchange(exchange)
    return exchange_map_em_flag.get(exchange, exchange)


def to_em_fq_flag(adjust_type: AdjustType):
    adjust_type = AdjustType(adjust_type)
    if adjust_type == AdjustType.bfq:
        return 0
    if adjust_type == AdjustType.qfq:
        return 1
    if adjust_type == AdjustType.hfq:
        return 2


def to_em_level_flag(level: IntervalLevel):
    level = IntervalLevel(level)
    if level == IntervalLevel.LEVEL_5MIN:
        return 5
    if level == IntervalLevel.LEVEL_15MIN:
        return 15
    elif level == IntervalLevel.LEVEL_30MIN:
        return 30
    elif level == IntervalLevel.LEVEL_1HOUR:
        return 60
    elif level == IntervalLevel.LEVEL_1DAY:
        return 101
    elif level == IntervalLevel.LEVEL_1WEEK:
        return 102
    elif level == IntervalLevel.LEVEL_1MON:
        return 103

    assert False


def to_em_sec_id(entity_id):
    entity_type, exchange, code = decode_entity_id(entity_id)
    # 主力合约
    if entity_type == "future" and code[-1].isalpha():
        code = code + "m"
    if entity_type == "currency" and "CNYC" in code:
        return f"120.{code}"
    return f"{to_em_entity_flag(exchange)}.{code}"


def to_zvt_code(code):
    #  ('中证当月连续', '8|060120'),
    #  ('沪深当月连续', '8|040120'),
    #  ('上证当月连续', '8|070120'),
    #  ('十债当季连续', '8|110120'),
    #  ('五债当季连续', '8|050120'),
    #  ('二债当季连续', '8|130120')]
    if code == "060120":
        return "IC"
    elif code == "040120":
        return "IF"
    elif code == "070120":
        return "IH"
    elif code == "110120":
        return "T"
    elif code == "050120":
        return "TF"
    elif code == "130120":
        return "TS"
    return code


if __name__ == "__main__":
    # from pprint import pprint
    # pprint(get_free_holder_report_dates(code='000338'))
    # pprint(get_holder_report_dates(code='000338'))
    # pprint(get_holders(code='000338', end_date='2021-03-31'))
    # pprint(get_free_holders(code='000338', end_date='2021-03-31'))
    # pprint(get_ii_holder(code='000338', report_date='2021-03-31',
    #                      org_type=actor_type_to_org_type(ActorType.corporation)))
    # print(
    #     get_ii_summary(code="600519", report_date="2021-03-31", org_type=actor_type_to_org_type(ActorType.corporation))
    # )
    # df = get_kdata(entity_id="index_sz_399370", level="1wk")
    df = get_tradable_list(entity_type="cbond")
    print(df)
    # df = get_news("stock_sz_300999", ps=1)
    # print(df)
    # print(len(df))
    # df = get_tradable_list(entity_type="block")
    # df = get_tradable_list(entity_type="indexus")
    # df = get_tradable_list(entity_type="currency")
    # df = get_tradable_list(entity_type="index")
    # df = get_kdata(entity_id="index_us_SPX", level="1d")
    # print(df)
    # df = get_treasury_yield(pn=1, ps=50, fetch_all=False)
    # print(df)
    # df = get_future_list()
    # print(df)
    # df = get_kdata(entity_id="future_dce_I", level="1d")
    # print(df)
    # df = get_dragon_and_tiger(code="000989", start_date="2018-10-31")
    # df = get_dragon_and_tiger_list(start_date="2022-04-25")
    # # df = get_tradable_list()
    # # df_delist = df[df["name"].str.contains("退")]
    # print(df_delist[["id", "name"]].values.tolist())
    # print(get_block_stocks(block_id="block_cn_BK1144"))
    # df = get_tradable_list(entity_type="index")
    # print(df)
    # df = get_kdata(entity_id="stock_bj_873693", level="1d")
    # print(df)
    # print(get_controlling_shareholder(code="000338"))
    # events = get_events(entity_id="stock_sz_300684")
    # print(events)


# the __all__ is generated
__all__ = [
    "get_treasury_yield",
    "get_ii_holder_report_dates",
    "get_dragon_and_tiger_list",
    "get_dragon_and_tiger",
    "get_holder_report_dates",
    "get_free_holder_report_dates",
    "get_ii_holder",
    "get_ii_summary",
    "get_free_holders",
    "get_controlling_shareholder",
    "get_holders",
    "get_url",
    "get_exchange",
    "actor_type_to_org_type",
    "generate_filters",
    "get_em_data",
    "get_quotes",
    "get_kdata",
    "get_basic_info",
    "get_future_list",
    "get_tradable_list",
    "get_block_stocks",
    "get_news",
    "to_em_fc",
    "to_em_entity_flag",
    "to_em_fq_flag",
    "to_em_level_flag",
    "to_em_sec_id",
    "to_zvt_code",
]
