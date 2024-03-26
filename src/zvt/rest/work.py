# -*- coding: utf-8 -*-
from typing import List

from fastapi import APIRouter, Query, HTTPException

from zvt.contract.api import get_db_session
from zvt.tag.dataset.stock_tags import (
    StockTagsModel,
    StockTags,
    CreateStockTagsModel,
    TagsInfoModel,
    TagsInfo,
    CreateTagsInfoModel,
    SubTagsInfo,
    HiddenTagsInfo,
)
from zvt.utils import is_same_date, today, current_date, to_time_str
from zvt.utils.model_utils import update_model
import zvt.contract.api as contract_api

work_router = APIRouter(
    prefix="/api/work",
    tags=["work"],
    responses={404: {"description": "Not found"}},
)


@work_router.get("/get_tags_info", response_model=List[TagsInfoModel])
def get_tags_info():
    """
    Get tags info
    """
    with contract_api.DBSession(provider="zvt", data_schema=TagsInfo)() as session:
        tags_info: List[TagsInfo] = TagsInfo.query_data(session=session, return_type="domain")
        return tags_info


@work_router.get("/get_sub_tags_info", response_model=List[TagsInfoModel])
def get_sub_tags_info():
    """
    Get sub tags info
    """
    with contract_api.DBSession(provider="zvt", data_schema=SubTagsInfo)() as session:
        tags_info: List[SubTagsInfo] = SubTagsInfo.query_data(session=session, return_type="domain")
        return tags_info


@work_router.get("/get_hidden_tags_info", response_model=List[TagsInfoModel])
def get_tags_info():
    """
    Get hidden tags info
    """
    with contract_api.DBSession(provider="zvt", data_schema=TagsInfo)() as session:
        tags_info: List[HiddenTagsInfo] = HiddenTagsInfo.query_data(session=session, return_type="domain")
        return tags_info


def _create_tags_info(tags_info: CreateTagsInfoModel, tags_info_type="tags_info"):
    """
    Create tags info
    """
    if tags_info_type == "tags_info":
        data_schema = TagsInfo
    elif tags_info_type == "sub_tags_info":
        data_schema = SubTagsInfo
    elif tags_info_type == "hidden_tags_info":
        data_schema = HiddenTagsInfo
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


@work_router.post("/create_tags_info", response_model=TagsInfoModel)
def create_tags_info(tags_info: CreateTagsInfoModel):
    return _create_tags_info(tags_info, tags_info_type="tags_info")


@work_router.post("/create_sub_tags_info", response_model=TagsInfoModel)
def create_sub_tags_info(tags_info: CreateTagsInfoModel):
    return _create_tags_info(tags_info, tags_info_type="sub_tags_info")


@work_router.post("/create_hidden_tags_info", response_model=TagsInfoModel)
def create_hidden_tags_info(tags_info: CreateTagsInfoModel):
    return _create_tags_info(tags_info, tags_info_type="hidden_tags_info")


@work_router.get("/get_stock_tags", response_model=List[StockTagsModel])
def get_stock_tags(entity_ids: str = Query(None), history_data: bool = Query(False)):
    """
    Get entity tags
    """
    filters = []
    if not history_data:
        filters = filters + [StockTags.latest.is_(True)]
    if entity_ids:
        filters = filters + [StockTags.entity_id.in_(entity_ids.split(","))]
    with contract_api.DBSession(provider="zvt", data_schema=StockTags)() as session:
        tags: List[StockTags] = StockTags.query_data(
            session=session, filters=filters, return_type="domain", order=StockTags.timestamp.desc()
        )
        return tags


@work_router.post("/create_stock_tags", response_model=StockTagsModel)
def create_stock_tags(stock_tags: CreateStockTagsModel):
    """
    Set entity tags
    """
    with contract_api.DBSession(provider="zvt", data_schema=StockTags)() as session:
        entity_id = stock_tags.entity_id
        tags = {}
        sub_tags = {}
        timestamp = current_date()
        datas = StockTags.query_data(
            session=session, entity_id=entity_id, order=StockTags.timestamp.desc(), limit=1, return_type="domain"
        )
        if datas:
            current_stock_tags: StockTags = datas[0]
            if current_stock_tags.tags:
                tags = dict(current_stock_tags.tags)
            if current_stock_tags.sub_tags:
                sub_tags = dict(current_stock_tags.sub_tags)
            if is_same_date(current_stock_tags.timestamp, timestamp):
                stock_tags_db = current_stock_tags
            else:
                current_stock_tags.latest = False
                stock_tags_db = StockTags(
                    id=f"{entity_id}_{to_time_str(timestamp)}",
                    entity_id=entity_id,
                    timestamp=timestamp,
                )
                session.add(current_stock_tags)
        else:
            stock_tags_db = StockTags(
                id=f"{entity_id}_{to_time_str(timestamp)}",
                entity_id=entity_id,
                timestamp=timestamp,
            )

        update_model(stock_tags_db, stock_tags)
        tags[stock_tags.tag] = stock_tags.tag_reason
        if stock_tags.sub_tag:
            sub_tags[stock_tags.sub_tag] = stock_tags.sub_tag_reason

        stock_tags_db.latest = True
        # update
        stock_tags_db.tags = tags
        stock_tags_db.sub_tags = sub_tags
        session.add(stock_tags_db)
        session.commit()
        session.refresh(stock_tags_db)
        return stock_tags_db
