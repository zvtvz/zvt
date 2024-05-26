# -*- coding: utf-8 -*-
from typing import List, Optional

from fastapi import APIRouter, HTTPException

import zvt.contract.api as contract_api
import zvt.tag.tag_service as tag_service
from zvt.domain import Stock
from zvt.tag.tag_models import (
    TagInfoModel,
    CreateTagInfoModel,
    StockTagsModel,
    SimpleStockTagsModel,
    SetStockTagsModel,
    CreateStockPoolInfoModel,
    StockPoolInfoModel,
    CreateStockPoolsModel,
    StockPoolsModel,
    QueryStockTagStatsModel,
    StockTagStatsModel,
    QueryStockTagsModel,
    QuerySimpleStockTagsModel,
    ActivateSubTagsResultModel,
    ActivateSubTagsModel,
)
from zvt.tag.tag_schemas import StockTags, MainTagInfo, SubTagInfo, HiddenTagInfo, StockPoolInfo, StockPools
from zvt.utils import current_date, to_time_str

work_router = APIRouter(
    prefix="/api/work",
    tags=["work"],
    responses={404: {"description": "Not found"}},
)


@work_router.post("/create_stock_pool_info", response_model=StockPoolInfoModel)
def create_stock_pool_info(create_stock_pool_info_model: CreateStockPoolInfoModel):
    return tag_service.build_stock_pool_info(create_stock_pool_info_model, timestamp=current_date())


@work_router.get("/get_stock_pool_info", response_model=List[StockPoolInfoModel])
def get_stock_pool_info():
    with contract_api.DBSession(provider="zvt", data_schema=StockPoolInfo)() as session:
        stock_pool_info: List[StockPoolInfo] = StockPoolInfo.query_data(session=session, return_type="domain")
        return stock_pool_info


@work_router.post("/create_stock_pools", response_model=StockPoolsModel)
def create_stock_pools(create_stock_pools_model: CreateStockPoolsModel):
    return tag_service.build_stock_pool(create_stock_pools_model, current_date())


@work_router.get("/get_stock_pools", response_model=Optional[StockPoolsModel])
def get_stock_pools(stock_pool_name: str):
    with contract_api.DBSession(provider="zvt", data_schema=StockPools)() as session:
        stock_pools: List[StockPools] = StockPools.query_data(
            session=session,
            filters=[StockPools.stock_pool_name == stock_pool_name],
            order=StockPools.timestamp.desc(),
            limit=1,
            return_type="domain",
        )
        if stock_pools:
            return stock_pools[0]
        return None


@work_router.get("/get_main_tag_info", response_model=List[TagInfoModel])
def get_main_tag_info():
    """
    Get main_tag info
    """
    with contract_api.DBSession(provider="zvt", data_schema=MainTagInfo)() as session:
        tags_info: List[MainTagInfo] = MainTagInfo.query_data(session=session, return_type="domain")
        return tags_info


@work_router.get("/get_sub_tag_info", response_model=List[TagInfoModel])
def get_sub_tag_info():
    """
    Get sub_tag info
    """
    with contract_api.DBSession(provider="zvt", data_schema=SubTagInfo)() as session:
        tags_info: List[SubTagInfo] = SubTagInfo.query_data(session=session, return_type="domain")
        return tags_info


@work_router.get("/get_hidden_tag_info", response_model=List[TagInfoModel])
def get_hidden_tag_info():
    """
    Get hidden_tag info
    """
    with contract_api.DBSession(provider="zvt", data_schema=MainTagInfo)() as session:
        tags_info: List[HiddenTagInfo] = HiddenTagInfo.query_data(session=session, return_type="domain")
        return tags_info


def _create_tag_info(tags_info: CreateTagInfoModel, tags_info_type="main_tag"):
    """
    Create tags info
    """
    if tags_info_type == "main_tag":
        data_schema = MainTagInfo
    elif tags_info_type == "sub_tag":
        data_schema = SubTagInfo
    elif tags_info_type == "hidden_tag":
        data_schema = HiddenTagInfo
    else:
        assert False

    with contract_api.DBSession(provider="zvt", data_schema=data_schema)() as session:
        current_tags_info = data_schema.query_data(
            session=session, filters=[data_schema.tag == tags_info.tag], return_type="domain"
        )
        if current_tags_info:
            raise HTTPException(status_code=409, detail=f"This tag has been registered in {tags_info_type}")
        timestamp = current_date()
        entity_id = "admin"
        tags_info_db = data_schema(
            id=f"admin_{to_time_str(timestamp)}_{tags_info.tag}",
            entity_id=entity_id,
            timestamp=timestamp,
            tag=tags_info.tag,
            tag_reason=tags_info.tag_reason,
        )
        session.add(tags_info_db)
        session.commit()
        session.refresh(tags_info_db)
        return tags_info_db


@work_router.post("/create_main_tag_info", response_model=TagInfoModel)
def create_main_tag_info(tag_info: CreateTagInfoModel):
    return _create_tag_info(tag_info, tags_info_type="main_tag")


@work_router.post("/create_sub_tag_info", response_model=TagInfoModel)
def create_sub_tag_info(tag_info: CreateTagInfoModel):
    return _create_tag_info(tag_info, tags_info_type="sub_tag")


@work_router.post("/create_hidden_tag_info", response_model=TagInfoModel)
def create_hidden_tag_info(tag_info: CreateTagInfoModel):
    return _create_tag_info(tag_info, tags_info_type="hidden_tag")


@work_router.post("/query_stock_tags", response_model=List[StockTagsModel])
def query_stock_tags(query_stock_tags_model: QueryStockTagsModel):
    """
    Get entity tags
    """
    filters = [StockTags.entity_id.in_(query_stock_tags_model.entity_ids)]

    with contract_api.DBSession(provider="zvt", data_schema=StockTags)() as session:
        tags: List[StockTags] = StockTags.query_data(
            session=session, filters=filters, return_type="domain", order=StockTags.timestamp.desc()
        )
        tags_dict = {tag.entity_id: tag for tag in tags}
        sorted_tags = [tags_dict[entity_id] for entity_id in query_stock_tags_model.entity_ids]
        return sorted_tags


@work_router.post("/query_simple_stock_tags", response_model=List[SimpleStockTagsModel])
def query_simple_stock_tags(query_simple_stock_tags_model: QuerySimpleStockTagsModel):
    """
    Get simple entity tags
    """

    entity_ids = query_simple_stock_tags_model.entity_ids

    filters = [StockTags.entity_id.in_(entity_ids)]
    with contract_api.DBSession(provider="zvt", data_schema=StockTags)() as session:
        tags: List[dict] = StockTags.query_data(
            session=session, filters=filters, return_type="dict", order=StockTags.timestamp.desc()
        )
        entity_tag_map = {item["entity_id"]: item for item in tags}
        result_tags = []
        stocks = Stock.query_data(provider="em", entity_ids=[tag["entity_id"] for tag in tags], return_type="domain")
        stocks_map = {item.entity_id: item for item in stocks}
        for entity_id in entity_ids:
            tag = entity_tag_map.get(entity_id)
            tag["name"] = stocks_map.get(entity_id).name
            result_tags.append(tag)
        return result_tags


@work_router.post("/set_stock_tags", response_model=StockTagsModel)
def set_stock_tags(set_stock_tags_model: SetStockTagsModel):
    """
    Set stock tags
    """
    return tag_service.build_stock_tags(
        set_stock_tags_model=set_stock_tags_model, timestamp=current_date(), set_by_user=True
    )


@work_router.post("/build_stock_tags", response_model=List[StockTagsModel])
def build_stock_tags(set_stock_tags_model_list: List[SetStockTagsModel]):
    """
    Set stock tags in batch
    """
    return [
        tag_service.build_stock_tags(
            set_stock_tags_model=set_stock_tags_model, timestamp=current_date(), set_by_user=True
        )
        for set_stock_tags_model in set_stock_tags_model_list
    ]


@work_router.post("/query_stock_tag_stats", response_model=List[StockTagStatsModel])
def query_stock_tag_stats(query_stock_tag_stats_model: QueryStockTagStatsModel):
    """
    Get stock tag stats
    """

    return tag_service.query_stock_tag_stats(query_stock_tag_stats_model=query_stock_tag_stats_model)


@work_router.post("/activate_sub_tags", response_model=ActivateSubTagsResultModel)
def activate_sub_tags(activate_sub_tags_model: ActivateSubTagsModel):
    """
    Activate sub tags
    """

    return tag_service.activate_main_tag_by_sub_tags(activate_sub_tags_model=activate_sub_tags_model)
