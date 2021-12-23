# -*- coding: utf-8 -*-
import logging
import time

import pandas as pd
import requests

from zvt.domain import IndexCategory
from zvt.recorders.consts import DEFAULT_HEADER
from zvt.utils import to_pd_timestamp

logger = logging.getLogger(__name__)

original_page_url = "http://www.cnindex.com.cn/zh_indices/sese/index.html?act_menu=1&index_type=-1"
url = "http://www.cnindex.net.cn/index/indexList?channelCode={}&rows=1000&pageNum=1"

# 中证指数 抓取 风格指数 行业指数 规模指数 基金指数
cni_category_map_url = {
    IndexCategory.style: url.format("202"),
    IndexCategory.industry: url.format("201"),
    IndexCategory.scope: url.format("200"),
    IndexCategory.fund: url.format("207"),
}

# 深证指数 只取规模指数
sz_category_map_url = {
    IndexCategory.scope: url.format("100"),
}


def _get_resp_data(resp: requests.Response):
    resp.raise_for_status()
    return resp.json()["data"]


def get_cn_index(index_type="cni", category=IndexCategory.style):
    if index_type == "cni":
        category_map_url = cni_category_map_url
    elif index_type == "sz":
        category_map_url = sz_category_map_url
    else:
        logger.error(f"not support index_type: {index_type}")
        assert False

    requests_session = requests.Session()

    url = category_map_url.get(category)

    resp = requests_session.get(url, headers=DEFAULT_HEADER)

    results = _get_resp_data(resp)["rows"]
    # e.g
    # amount: 277743699997.9
    # closeingPoint: 6104.7592
    # docchannel: 1039
    # freeMarketValue: 10794695531696.15
    # id: 142
    # indexcode: "399370"
    # indexename: "CNI Growth"
    # indexfullcname: "国证1000成长指数"
    # indexfullename: "CNI 1000 Growth Index"
    # indexname: "国证成长"
    # indexsource: "1"
    # indextype: "202"
    # pb: 5.34
    # peDynamic: 29.8607
    # peStatic: 33.4933
    # percent: 0.0022
    # prefixmonth: null
    # realtimemarket: "1"
    # remark: ""
    # sampleshowdate: null
    # samplesize: 332
    # showcnindex: "1"
    # totalMarketValue: 23113641352198.32
    the_list = []

    logger.info(f"category: {category} ")
    logger.info(f"results: {results} ")
    for i, result in enumerate(results):
        logger.info(f"to {i}/{len(results)}")
        code = result["indexcode"]
        info_resp = requests_session.get(f"http://www.cnindex.net.cn/index-intro?indexcode={code}")
        # fbrq: "2010-01-04"
        # jd: 1000
        # jr: "2002-12-31"
        # jsfs: "自由流通市值"
        # jsjj: "国证成长由国证1000指数样本股中成长风格突出的股票组成，为投资者提供更丰富的指数化投资工具。"
        # qzsx: null
        # typl: 2
        # xyfw: "沪深A股"
        # xygz: "在国证1000指数样本股中，选取主营业务收入增长率、净利润增长率和净资产收益率综合排名前332只"
        index_info = _get_resp_data(info_resp)
        name = result["indexname"]
        entity_id = f"index_sz_{code}"
        index_item = {
            "id": entity_id,
            "entity_id": entity_id,
            "timestamp": to_pd_timestamp(index_info["jr"]),
            "entity_type": "index",
            "exchange": "sz",
            "code": code,
            "name": name,
            "category": category.value,
            "list_date": to_pd_timestamp(index_info["fbrq"]),
            "base_point": index_info["jd"],
            "publisher": "cnindex",
        }
        logger.info(index_item)
        the_list.append(index_item)
        time.sleep(3)
    if the_list:
        return pd.DataFrame.from_records(the_list)


if __name__ == "__main__":
    df = get_cn_index()
    print(df)
# the __all__ is generated
__all__ = ["get_cn_index"]
