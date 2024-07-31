# -*- coding: utf-8 -*-
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

from zvt.contract import IntervalLevel
from zvt.trader import TradingSignalType
from zvt.utils.time_utils import date_time_by_interval, current_date


class FactorRequestModel(BaseModel):
    factor_name: str
    entity_ids: Optional[List[str]]
    data_provider: str = Field(default="em")
    start_timestamp: datetime = Field(default=date_time_by_interval(current_date(), -365))
    level: IntervalLevel = Field(default=IntervalLevel.LEVEL_1DAY)


class TradingSignalModel(BaseModel):
    entity_id: str
    happen_timestamp: datetime
    due_timestamp: datetime
    trading_level: IntervalLevel = Field(default=IntervalLevel.LEVEL_1DAY)
    trading_signal_type: TradingSignalType
    position_pct: Optional[float] = Field(default=0.2)
    order_amount: Optional[float] = Field(default=None)
    order_money: Optional[float] = Field(default=None)


class FactorResultModel(BaseModel):
    entity_ids: Optional[List[str]]
    tag_reason: str


# the __all__ is generated
__all__ = ["FactorRequestModel", "TradingSignalModel", "FactorResultModel"]
