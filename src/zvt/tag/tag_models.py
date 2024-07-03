# -*- coding: utf-8 -*-
from typing import Dict, Union, List, Optional

from pydantic import field_validator, Field
from pydantic_core.core_schema import ValidationInfo

from zvt.contract.model import MixinModel, CustomModel
from zvt.tag.common import StockPoolType, TagType, TagStatsQueryType
from zvt.tag.tag_utils import get_main_tags, get_sub_tags, get_hidden_tags, get_stock_pool_names


class TagInfoModel(MixinModel):
    tag: str
    tag_reason: Optional[str] = None


class CreateTagInfoModel(CustomModel):
    tag: str
    tag_reason: Optional[str] = None


class StockTagsModel(MixinModel):
    main_tag: str
    main_tag_reason: Optional[str] = None
    main_tags: Dict[str, str]

    sub_tag: Union[str, None]
    sub_tag_reason: Optional[str] = None
    sub_tags: Union[Dict[str, str], None]

    active_hidden_tags: Union[Dict[str, str], None]
    hidden_tags: Union[Dict[str, str], None]
    set_by_user: bool = False


class SimpleStockTagsModel(CustomModel):
    entity_id: str
    name: str
    main_tag: str
    main_tag_reason: Optional[str] = None
    main_tags: Dict[str, str]
    sub_tag: Union[str, None]
    sub_tag_reason: Optional[str] = None
    sub_tags: Union[Dict[str, str], None]
    active_hidden_tags: Union[Dict[str, str], None]


class QueryStockTagsModel(CustomModel):
    entity_ids: List[str]


class QuerySimpleStockTagsModel(CustomModel):
    entity_ids: List[str]


class BatchSetStockTagsModel(CustomModel):
    entity_ids: List[str]
    tag: str
    tag_reason: Optional[str] = None
    tag_type: TagType


class TagParameter(CustomModel):
    main_tag: str
    main_tag_reason: Optional[str] = None
    sub_tag: Optional[str] = None
    sub_tag_reason: Optional[str] = None


class SetStockTagsModel(CustomModel):
    entity_id: str
    main_tag: str
    main_tag_reason: Optional[str] = None
    sub_tag: Union[str, None]
    sub_tag_reason: Optional[str] = None
    active_hidden_tags: Union[Dict[str, str], None]

    @field_validator("main_tag")
    @classmethod
    def main_tag_must_be_in(cls, v: str) -> str:
        if v not in get_main_tags():
            raise ValueError(f"main_tag: {v} must be created at main_tag_info at first")
        return v

    @field_validator("sub_tag")
    @classmethod
    def sub_tag_must_be_in(cls, v: str) -> str:
        if v not in get_sub_tags():
            raise ValueError(f"sub_tag: {v} must be created at sub_tag_info at first")
        return v

    @field_validator("active_hidden_tags")
    @classmethod
    def hidden_tag_must_be_in(cls, v: Union[Dict[str, str], None]) -> Union[Dict[str, str], None]:
        if v:
            for item in v.keys():
                if item not in get_hidden_tags():
                    raise ValueError(f"hidden_tag: {v} must be created at hidden_tag_info at first")
        return v


class StockPoolModel(MixinModel):
    stock_pool_name: str
    entity_ids: List[str]


class StockPoolInfoModel(MixinModel):
    stock_pool_type: StockPoolType
    stock_pool_name: str


class CreateStockPoolInfoModel(CustomModel):
    stock_pool_type: StockPoolType
    stock_pool_name: str

    @field_validator("stock_pool_name")
    @classmethod
    def stock_pool_name_existed(cls, v: str) -> str:
        if v in get_stock_pool_names():
            raise ValueError(f"stock_pool_name: {v} has been used")
        return v


class StockPoolsModel(MixinModel):
    stock_pool_name: str
    entity_ids: List[str]


class CreateStockPoolsModel(CustomModel):
    stock_pool_name: str
    entity_ids: List[str]

    @field_validator("stock_pool_name")
    @classmethod
    def stock_pool_name_must_be_in(cls, v: str) -> str:
        if v:
            if v not in get_stock_pool_names():
                raise ValueError(f"stock_pool_name: {v} must be created at stock_pool_info at first")
        return v


class QueryStockTagStatsModel(CustomModel):
    stock_pool_name: Optional[str] = None
    entity_ids: Optional[List[str]] = None
    query_type: Optional[TagStatsQueryType] = Field(default=TagStatsQueryType.details)

    @field_validator("stock_pool_name", "entity_ids")
    @classmethod
    def phone_or_mobile_must_set_only_one(cls, v, validation_info: ValidationInfo, **kwargs):
        if validation_info.field_name == "stock_pool_name":
            other_field = "entity_ids"
        else:
            other_field = "stock_pool_name"

        other_value = kwargs.get(other_field)

        if v and other_value:
            raise ValueError(f"Only one of 'stock_pool_name' or 'entity_ids' should be set.")
        elif not v and not other_value:
            raise ValueError("Either 'stock_pool_name' or 'entity_ids' must be set.")

        return v

    @field_validator("stock_pool_name")
    @classmethod
    def stock_pool_name_must_be_in(cls, v: str) -> str:
        if v:
            if v not in get_stock_pool_names():
                raise ValueError(f"stock_pool_name: {v} not existed")
        return v


class StockTagDetailsModel(CustomModel):
    entity_id: str
    main_tag: str
    sub_tag: Union[str, None]
    hidden_tags: Union[List[str], None]

    #: 代码
    code: str
    #: 名字
    name: str
    #: 减持
    recent_reduction: Optional[bool] = Field(default=None)
    #: 增持
    recent_acquisition: Optional[bool] = Field(default=None)
    #: 解禁
    recent_unlock: Optional[bool] = Field(default=None)
    #: 增发配股
    recent_additional_or_rights_issue: Optional[bool] = Field(default=None)
    #: 业绩利好
    recent_positive_earnings_news: Optional[bool] = Field(default=None)
    #: 业绩利空
    recent_negative_earnings_news: Optional[bool] = Field(default=None)
    #: 上榜次数
    recent_dragon_and_tiger_count: Optional[int] = Field(default=None)
    #: 违规行为
    recent_violation_alert: Optional[bool] = Field(default=None)
    #: 利好
    recent_positive_news: Optional[bool] = Field(default=None)
    #: 利空
    recent_negative_news: Optional[bool] = Field(default=None)
    #: 新闻总结
    recent_news_summary: Optional[Dict[str, str]] = Field(default=None)


class StockTagStatsModel(MixinModel):
    main_tag: str
    turnover: Optional[float] = Field(default=None)
    entity_count: Optional[int] = Field(default=None)
    position: Optional[int] = Field(default=None)
    is_main_line: Optional[bool] = Field(default=None)
    main_line_continuous_days: Optional[int] = Field(default=None)
    entity_ids: Optional[List[str]] = Field(default=None)
    stock_details: Optional[List[StockTagDetailsModel]] = Field(default=None)


class ActivateSubTagsModel(CustomModel):
    sub_tags: List[str]


class ActivateSubTagsResultModel(CustomModel):
    tag_entity_ids: Dict[str, Union[List[str], None]]


# the __all__ is generated
__all__ = [
    "TagInfoModel",
    "CreateTagInfoModel",
    "StockTagsModel",
    "SimpleStockTagsModel",
    "QueryStockTagsModel",
    "QuerySimpleStockTagsModel",
    "BatchSetStockTagsModel",
    "TagParameter",
    "SetStockTagsModel",
    "StockPoolModel",
    "StockPoolInfoModel",
    "CreateStockPoolInfoModel",
    "StockPoolsModel",
    "CreateStockPoolsModel",
    "QueryStockTagStatsModel",
    "StockTagDetailsModel",
    "StockTagStatsModel",
    "ActivateSubTagsModel",
    "ActivateSubTagsResultModel",
]
