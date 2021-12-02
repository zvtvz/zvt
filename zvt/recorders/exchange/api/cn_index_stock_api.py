# -*- coding: utf-8 -*-
import logging

import pandas as pd
import requests

from zvt.api.utils import china_stock_code_to_id, value_to_pct, value_multiply
from zvt.recorders.consts import DEFAULT_HEADER
from zvt.utils.time_utils import to_pd_timestamp, to_time_str, TIME_FORMAT_MON

logger = logging.getLogger(__name__)

original_page_url = "http://www.cnindex.com.cn/module/index-detail.html?act_menu=1&indexCode=399001"
url = "http://www.cnindex.net.cn/sample-detail/detail?indexcode={}&dateStr={}&pageNum=1&rows=5000"


def _get_resp_data(resp: requests.Response):
    resp.raise_for_status()
    return resp.json()["data"]


def get_cn_index_stock(code, timestamp, name=None):
    entity_type = "index"
    exchange = "sz"
    entity_id = f"{entity_type}_{exchange}_{code}"
    data_str = to_time_str(timestamp, TIME_FORMAT_MON)
    resp = requests.get(url.format(code, data_str), headers=DEFAULT_HEADER)
    data = _get_resp_data(resp)
    if not data:
        return
    results = _get_resp_data(resp)["rows"]

    the_list = []
    for result in results:
        # date: 1614268800000
        # dateStr: "2021-02-26"
        # freeMarketValue: 10610.8
        # indexcode: "399370"
        # market: null
        # seccode: "600519"
        # secname: "贵州茅台"
        # totalMarketValue: 26666.32
        # trade: "主要消费"
        # weight: 10.01
        stock_code = result["seccode"]
        stock_name = result["secname"]
        stock_id = china_stock_code_to_id(stock_code)

        the_list.append(
            {
                "id": "{}_{}_{}".format(entity_id, result["dateStr"], stock_id),
                "entity_id": entity_id,
                "entity_type": entity_type,
                "exchange": exchange,
                "code": code,
                "name": name,
                "timestamp": to_pd_timestamp(result["dateStr"]),
                "stock_id": stock_id,
                "stock_code": stock_code,
                "stock_name": stock_name,
                "proportion": value_to_pct(result["weight"], 0),
                "market_cap": value_multiply(result["freeMarketValue"], 100000000, 0),
            }
        )
    if the_list:
        df = pd.DataFrame.from_records(the_list)
        return df


if __name__ == "__main__":
    df = get_cn_index_stock(timestamp="2021-08-01", code="399370", name="国证成长")
    print(df)
# the __all__ is generated
__all__ = ["get_cn_index_stock"]
