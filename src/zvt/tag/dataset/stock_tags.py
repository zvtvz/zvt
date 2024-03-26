# -*- coding: utf-8 -*-
from typing import Dict, List, Union

from pydantic import BaseModel
from sqlalchemy import Column, String, JSON, Boolean
from sqlalchemy.orm import declarative_base

from zvt.contract import Mixin
from zvt.contract.model import MixinModel
from zvt.contract.register import register_schema

StockTagsBase = declarative_base()


class TagsInfo(StockTagsBase, Mixin):
    __tablename__ = "tags_info"

    tag = Column(String, unique=True)
    tag_reason = Column(String)


class SubTagsInfo(StockTagsBase, Mixin):
    __tablename__ = "sub_tags_info"

    tag = Column(String, unique=True)
    tag_reason = Column(String)


class HiddenTagsInfo(StockTagsBase, Mixin):
    __tablename__ = "hidden_tags_info"

    tag = Column(String, unique=True)
    tag_reason = Column(String)


class TagsInfoModel(MixinModel):
    tag: str
    tag_reason: str


class CreateTagsInfoModel(BaseModel):
    tag: str
    tag_reason: str


class StockTags(StockTagsBase, Mixin):
    """
    Schema for storing stock tags
    """

    __tablename__ = "stock_tags"

    tag = Column(String)
    tag_reason = Column(String)
    tags = Column(JSON)

    sub_tag = Column(String)
    sub_tag_reason = Column(String)
    sub_tags = Column(JSON)

    active_hidden_tags = Column(JSON)
    hidden_tags = Column(JSON)
    set_by_user = Column(Boolean, default=False)
    #: 每个标的最后更新的记录
    latest = Column(Boolean, default=False)


class StockTagsModel(MixinModel):
    tag: str
    tag_reason: str
    tags: Dict[str, str]

    sub_tag: Union[str, None]
    sub_tag_reason: Union[str, None]
    sub_tags: Union[Dict[str, str], None]

    active_hidden_tags: Union[List[str], None]
    hidden_tags: Union[Dict[str, str], None]
    set_by_user: bool = False


class CreateStockTagsModel(BaseModel):
    entity_id: str
    tag: str
    tag_reason: str
    sub_tag: Union[str, None]
    sub_tag_reason: Union[str, None]
    active_hidden_tags: Union[List[str], None]
    hidden_tags: Union[Dict[str, str], None]


register_schema(providers=["zvt"], db_name="stock_tags", schema_base=StockTagsBase)
# the __all__ is generated
__all__ = [
    "TagsInfo",
    "SubTagsInfo",
    "HiddenTagsInfo",
    "TagsInfoModel",
    "CreateTagsInfoModel",
    "StockTags",
    "StockTagsModel",
    "CreateStockTagsModel",
]
