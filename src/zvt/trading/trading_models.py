# -*- coding: utf-8 -*-
from datetime import datetime
from typing import Union, List, Optional

from pydantic import BaseModel, field_validator, Field

from zvt.common.query_models import TimeRange, OrderByType
from zvt.contract.model import MixinModel, CustomModel
from zvt.tag.tag_utils import get_stock_pool_names
from zvt.trader import TradingSignalType
from zvt.trading.common import ExecutionStatus
from zvt.utils.time_utils import tomorrow_date, to_pd_timestamp


class QueryStockQuoteSettingModel(CustomModel):
    stock_pool_name: Optional[str] = Field(default=None)
    main_tags: Optional[List[str]] = Field(default=None)


class BuildQueryStockQuoteSettingModel(BaseModel):
    stock_pool_name: str
    main_tags: Optional[List[str]] = Field(default=None)

    @field_validator("stock_pool_name")
    @classmethod
    def stock_pool_name_existed(cls, v: str) -> str:
        if v not in get_stock_pool_names():
            raise ValueError(f"Invalid stock_pool_name: {v}")
        return v


class QueryTagQuoteModel(CustomModel):
    stock_pool_name: str
    main_tags: List[str]


class QueryStockQuoteModel(CustomModel):

    main_tag: Optional[str] = Field(default=None)
    entity_ids: Optional[List[str]] = Field(default=None)
    stock_pool_name: Optional[str] = Field(default=None)
    # the amount is not huge, just ignore now
    limit: int = Field(default=100)
    order_by_type: Optional[OrderByType] = Field(default=OrderByType.desc)
    order_by_field: Optional[str] = Field(default="change_pct")


class StockQuoteModel(MixinModel):
    #: 代码
    code: str
    #: 名字
    name: str

    #: UNIX时间戳
    time: int
    #: 最新价
    price: float
    # 涨跌幅
    change_pct: float
    # 成交金额
    turnover: float
    # 换手率
    turnover_rate: float
    #: 是否涨停
    is_limit_up: bool
    #: 封涨停金额
    limit_up_amount: Optional[float] = Field(default=None)
    #: 是否跌停
    is_limit_down: bool
    #: 封跌停金额
    limit_down_amount: Optional[float] = Field(default=None)
    #: 5挡卖单金额
    ask_amount: float
    #: 5挡买单金额
    bid_amount: float
    #: 流通市值
    float_cap: float
    #: 总市值
    total_cap: float

    main_tag: str = Field(default=None)
    sub_tag: Union[str, None] = Field(default=None)
    hidden_tags: Union[List[str], None] = Field(default=None)


class TagQuoteStatsModel(CustomModel):
    main_tag: str
    #: 涨停数
    limit_up_count: int
    #: 跌停数
    limit_down_count: int
    #: 上涨数
    up_count: int
    #: 下跌数
    down_count: int
    #: 涨幅
    change_pct: float
    #: 成交额
    turnover: float


class StockQuoteStatsModel(CustomModel):
    #: 涨停数
    limit_up_count: int
    #: 跌停数
    limit_down_count: int
    #: 上涨数
    up_count: int
    #: 下跌数
    down_count: int
    #: 涨幅
    change_pct: float
    #: 成交额
    turnover: float

    quotes: List[StockQuoteModel]


class TradingPlanModel(MixinModel):
    stock_id: str
    stock_code: str
    stock_name: str
    # 执行交易日
    trading_date: datetime
    # 预期开盘涨跌幅
    expected_open_pct: float
    buy_price: Optional[float]
    sell_price: Optional[float]
    # 操作理由
    trading_reason: str
    # 交易信号
    trading_signal_type: TradingSignalType
    # 执行状态
    status: ExecutionStatus = Field(default=ExecutionStatus.init)
    # 复盘
    review: Optional[str]


class BuildTradingPlanModel(BaseModel):
    stock_id: str
    # 执行交易日
    trading_date: datetime
    # 预期开盘涨跌幅
    expected_open_pct: float
    buy_price: Optional[float]
    sell_price: Optional[float]
    # 操作理由
    trading_reason: str
    # 交易信号
    trading_signal_type: TradingSignalType

    @field_validator("trading_date")
    @classmethod
    def trading_date_must_be_future(cls, v: str) -> str:
        if to_pd_timestamp(v) < tomorrow_date():
            raise ValueError(f"trading_date: {v} must set to future trading date")
        return v


class QueryTradingPlanModel(BaseModel):
    time_range: TimeRange


# the __all__ is generated
__all__ = [
    "QueryTagQuoteModel",
    "QueryStockQuoteSettingModel",
    "BuildQueryStockQuoteSettingModel",
    "QueryStockQuoteModel",
    "StockQuoteModel",
    "StockQuoteStatsModel",
    "TradingPlanModel",
    "BuildTradingPlanModel",
    "QueryTradingPlanModel",
]
