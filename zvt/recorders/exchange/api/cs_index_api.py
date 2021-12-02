# -*- coding: utf-8 -*-
import logging

import pandas as pd
import requests

from zvt.domain import IndexCategory
from zvt.recorders.consts import DEFAULT_HEADER
from zvt.utils import to_pd_timestamp

logger = logging.getLogger(__name__)

original_page_url = "https://www.csindex.com.cn/zh-CN#/indices/family/list?index_series=2"

url = "https://www.csindex.com.cn/csindex-home/index-list/query-index-item"

index_category_map = {IndexCategory.scope: "17", IndexCategory.industry: "18", IndexCategory.style: "19"}


def _get_resp_data(resp: requests.Response):
    resp.raise_for_status()
    return resp.json()["data"]


def _get_params(index_type, category: IndexCategory):
    if index_type == "csi":
        index_series = ["1"]
    elif index_type == "sh":
        index_series = ["2"]
    else:
        logger.warning(f"not support index type: {index_type}")
        assert False
    index_classify = index_category_map.get(category)

    return {
        "sorter": {"sortField": "index_classify", "sortOrder": "asc"},
        "pager": {"pageNum": 1, "pageSize": 10},
        "indexFilter": {
            "ifCustomized": None,
            "ifTracked": None,
            "ifWeightCapped": None,
            "indexCompliance": None,
            "hotSpot": None,
            "indexClassify": [index_classify],
            "currency": None,
            "region": None,
            "indexSeries": index_series,
            "undefined": None,
        },
    }


def get_cs_index(index_type="sh"):
    if index_type == "csi":
        category_list = [IndexCategory.scope, IndexCategory.industry, IndexCategory.style]
    elif index_type == "sh":
        category_list = [IndexCategory.scope]
    else:
        logger.warning(f"not support index type: {index_type}")
        assert False

    requests_session = requests.Session()

    for category in category_list:
        data = _get_params(index_type=index_type, category=category)
        print(data)
        resp = requests_session.post(url, headers=DEFAULT_HEADER, json=data)

        print(resp)
        results = _get_resp_data(resp)
        the_list = []

        logger.info(f"category: {category} ")
        logger.info(f"results: {results} ")
        for i, result in enumerate(results):
            logger.info(f"to {i}/{len(results)}")
            code = result["indexCode"]

            info_url = f"https://www.csindex.com.cn/csindex-home/indexInfo/index-basic-info/{code}"
            info = _get_resp_data(requests_session.get(info_url))

            name = result["indexName"]
            entity_id = f"index_sh_{code}"
            index_item = {
                "id": entity_id,
                "entity_id": entity_id,
                "timestamp": to_pd_timestamp(info["basicDate"]),
                "entity_type": "index",
                "exchange": "sh",
                "code": code,
                "name": name,
                "category": category.value,
                "list_date": to_pd_timestamp(result["publishDate"]),
                "base_point": info["basicIndex"],
                "publisher": "csindex",
            }
            logger.info(index_item)
            the_list.append(index_item)
        if the_list:
            return pd.DataFrame.from_records(the_list)


if __name__ == "__main__":
    df = get_cs_index()
    print(df)
# the __all__ is generated
__all__ = ["get_cs_index"]
