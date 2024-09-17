# -*- coding: utf-8 -*-
import json
import os
from typing import List, Dict

import pandas as pd

from zvt import zvt_env
from zvt.contract.api import df_to_db
from zvt.domain import Block
from zvt.tag.common import StockPoolType
from zvt.tag.tag_schemas import MainTagInfo, SubTagInfo, HiddenTagInfo, StockPoolInfo, IndustryInfo


def _get_default_industry_main_tag_mapping() -> Dict[str, str]:
    with open(os.path.join(zvt_env["resource_path"], "industry_main_tag_mapping.json"), encoding="utf-8") as f:
        return json.load(f)


def _get_default_main_tag_industry_mapping() -> Dict[str, List[str]]:
    mapping = _get_default_industry_main_tag_mapping()
    result = {}
    for industry, main_tag in mapping.items():
        result.setdefault(main_tag, [])
        result.get(main_tag).append(industry)
    return result


def _get_default_concept_main_tag_mapping() -> Dict[str, str]:
    with open(os.path.join(zvt_env["resource_path"], "concept_main_tag_mapping.json"), encoding="utf-8") as f:
        return json.load(f)


def _get_default_main_tag_concept_mapping() -> Dict[str, List[str]]:
    mapping = _get_default_concept_main_tag_mapping()
    result = {}
    for concept, main_tag in mapping.items():
        result.setdefault(main_tag, [])
        result.get(main_tag).append(concept)
    return result


def _get_initial_sub_tags() -> List[str]:
    return list(_get_default_concept_main_tag_mapping().keys())


def _get_industry_list():
    df = Block.query_data(
        filters=[Block.category == "industry"], columns=[Block.name], return_type="df", order=Block.timestamp.desc()
    )
    return df["name"].tolist()


def _get_concept_list():
    df = Block.query_data(
        filters=[Block.category == "concept"], columns=[Block.name], return_type="df", order=Block.timestamp.desc()
    )

    return df["name"].tolist()


def _check_missed_industry():
    current_industry_list = _get_default_industry_main_tag_mapping().keys()
    return list(set(_get_industry_list()) - set(current_industry_list))


def _check_missed_concept():
    current_concept_list = _get_default_concept_main_tag_mapping().keys()
    return list(set(_get_concept_list()) - set(current_concept_list))


def _get_initial_main_tag_info():
    timestamp = "2024-03-25"
    entity_id = "admin"

    from_industry = [
        {
            "id": f"{entity_id}_{main_tag}",
            "entity_id": entity_id,
            "timestamp": timestamp,
            "tag": main_tag,
            "tag_reason": f"来自这些行业:{industry}",
        }
        for main_tag, industry in _get_default_main_tag_industry_mapping().items()
    ]

    from_concept = []
    for tag, concepts in _get_default_main_tag_concept_mapping().items():
        if tag not in _get_default_main_tag_industry_mapping():
            from_concept.append(
                {
                    "id": f"{entity_id}_{tag}",
                    "entity_id": entity_id,
                    "timestamp": timestamp,
                    "tag": tag,
                    "tag_reason": f"来自这些概念:{','.join(concepts)}",
                }
            )

    return from_industry + from_concept


def _get_initial_industry_info():
    timestamp = "2024-03-25"
    entity_id = "admin"
    industry_info = [
        {
            "id": f"{entity_id}_{industry}",
            "entity_id": entity_id,
            "timestamp": timestamp,
            "industry_name": industry,
            "description": industry,
            "main_tag": main_tag,
        }
        for industry, main_tag in _get_default_industry_main_tag_mapping().items()
    ]
    return industry_info


def _get_initial_sub_tag_info():
    timestamp = "2024-03-25"
    entity_id = "admin"

    return [
        {
            "id": f"{entity_id}_{sub_tag}",
            "entity_id": entity_id,
            "timestamp": timestamp,
            "tag": sub_tag,
            "tag_reason": sub_tag,
            "main_tag": main_tag,
        }
        for sub_tag, main_tag in _get_default_concept_main_tag_mapping().items()
    ]


def _get_initial_stock_pool_info():
    timestamp = "2024-03-25"
    entity_id = "admin"
    return [
        {
            "id": f"{entity_id}_{stock_pool_name}",
            "entity_id": entity_id,
            "timestamp": timestamp,
            "stock_pool_type": StockPoolType.system.value,
            "stock_pool_name": stock_pool_name,
        }
        for stock_pool_name in ["main_line", "vol_up", "大局", "all"]
    ]


_hidden_tags = {
    "中字头": "央企，国资委控股",
    "核心资产": "高ROE 高现金流 高股息 低应收 低资本开支 低财务杠杆 有增长",
    "高股息": "高股息",
    "微盘股": "市值50亿以下",
    "次新股": "上市未满两年",
}


def _get_initial_hidden_tag_info():
    timestamp = "2024-03-25"
    entity_id = "admin"
    return [
        {
            "id": f"{entity_id}_{tag}",
            "entity_id": entity_id,
            "timestamp": timestamp,
            "tag": tag,
            "tag_reason": tag_reason,
        }
        for tag, tag_reason in _hidden_tags.items()
    ]


def build_initial_main_tag_info():
    main_tag_info_list = _get_initial_main_tag_info()
    df = pd.DataFrame.from_records(main_tag_info_list)
    df_to_db(df=df, data_schema=MainTagInfo, provider="zvt", force_update=False)


def build_initial_industry_info():
    initial_industry_info = _get_initial_industry_info()
    df = pd.DataFrame.from_records(initial_industry_info)
    df_to_db(df=df, data_schema=IndustryInfo, provider="zvt", force_update=False)


def build_initial_sub_tag_info(force_update=False):
    sub_tag_info_list = _get_initial_sub_tag_info()
    df = pd.DataFrame.from_records(sub_tag_info_list)
    df_to_db(df=df, data_schema=SubTagInfo, provider="zvt", force_update=force_update)


def build_initial_stock_pool_info():
    stock_pool_info_list = _get_initial_stock_pool_info()
    df = pd.DataFrame.from_records(stock_pool_info_list)
    df_to_db(df=df, data_schema=StockPoolInfo, provider="zvt", force_update=False)


def build_initial_hidden_tag_info():
    hidden_tag_info_list = _get_initial_hidden_tag_info()
    df = pd.DataFrame.from_records(hidden_tag_info_list)
    df_to_db(df=df, data_schema=HiddenTagInfo, provider="zvt", force_update=False)


def get_main_tags():
    df = MainTagInfo.query_data(columns=[MainTagInfo.tag])
    return df["tag"].tolist()


def get_main_tag_by_sub_tag(sub_tag):
    datas: List[SubTagInfo] = SubTagInfo.query_data(filters=[SubTagInfo.tag == sub_tag], return_type="domain")
    if datas:
        return datas[0].main_tag
    else:
        return _get_default_concept_main_tag_mapping().get(sub_tag, "其他")


def get_main_tag_by_industry(industry_name):
    datas: List[IndustryInfo] = IndustryInfo.query_data(
        filters=[IndustryInfo.industry_name == industry_name], return_type="domain"
    )
    if datas:
        return datas[0].main_tag
    else:
        _get_default_industry_main_tag_mapping().get(industry_name, "其他")


def get_sub_tags():
    df = SubTagInfo.query_data(columns=[SubTagInfo.tag])
    return df["tag"].tolist()


def get_hidden_tags():
    df = HiddenTagInfo.query_data(columns=[HiddenTagInfo.tag])
    return df["tag"].tolist()


def get_stock_pool_names():
    df = StockPoolInfo.query_data(columns=[StockPoolInfo.stock_pool_name])
    return df["stock_pool_name"].tolist()


def match_tag_by_type(alias, tag_type="main_tag"):
    if tag_type == "main_tag":
        tags = get_main_tags()
    elif tag_type == "sub_tag":
        tags = get_sub_tags()
    elif tag_type == "industry":
        tags = _get_industry_list()
    else:
        assert False

    max_intersection_length = 0
    max_tag = None

    for tag in tags:
        intersection_length = len(set(alias) & set(tag))
        # at least 2 same chars
        if intersection_length < 2:
            continue

        if intersection_length > max_intersection_length:
            max_intersection_length = intersection_length
            max_tag = tag

    return max_tag


def match_tag(alias):
    tag = match_tag_by_type(alias, tag_type="main_tag")
    if tag:
        return "main_tag", tag

    tag = match_tag_by_type(alias, tag_type="sub_tag")
    if tag:
        return "sub_tag", tag

    tag = match_tag_by_type(alias, tag_type="industry")
    if tag:
        return "main_tag", get_main_tag_by_industry(tag)

    return "new_tag", alias


if __name__ == "__main__":
    # with open("missed_concept.json", "w") as json_file:
    #     json.dump(check_missed_concept(), json_file, indent=2, ensure_ascii=False)
    # with open("missed_industry.json", "w") as json_file:
    #     json.dump(check_missed_industry(), json_file, indent=2, ensure_ascii=False)
    # print(industry_to_main_tag("光伏设备"))
    # result = {}
    # for main_tag, concepts in get_main_tag_industry_mapping().items():
    #     for tag in concepts:
    #         result[tag] = main_tag
    # with open("industry_main_tag_mapping.json", "w") as json_file:
    #     json.dump(result, json_file, indent=2, ensure_ascii=False)
    # build_initial_stock_pool_info()
    # build_initial_main_tag_info()
    build_initial_sub_tag_info(force_update=True)
    build_initial_industry_info()


# the __all__ is generated
__all__ = [
    "build_initial_main_tag_info",
    "build_initial_industry_info",
    "build_initial_sub_tag_info",
    "build_initial_stock_pool_info",
    "build_initial_hidden_tag_info",
    "get_main_tags",
    "get_main_tag_by_sub_tag",
    "get_main_tag_by_industry",
    "get_sub_tags",
    "get_hidden_tags",
    "get_stock_pool_names",
    "match_tag_by_type",
    "match_tag",
]
