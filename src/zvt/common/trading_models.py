# -*- coding: utf-8 -*-
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class PositionType(Enum):
    # 按整体仓位算
    normal = "normal"

    # 不管整体仓位多少
    # 按现金算
    cash = "cash"


class BuyParameter(BaseModel):
    entity_ids: List[str]
    position_type: PositionType = Field(default=PositionType.normal)
    position_pct: Optional[float] = Field(default=None)
    weights: Optional[List[float]] = Field(default=None)
    money_to_use: Optional[float] = Field(default=None)


class SellParameter(BaseModel):
    entity_ids: List[str]
    sell_pcts: Optional[List[float]] = Field(default=None)


class TradingResult(BaseModel):
    success_entity_ids: Optional[List[str]] = Field(default=None)
    failed_entity_ids: Optional[List[str]] = Field(default=None)


# the __all__ is generated
__all__ = ["PositionType", "BuyParameter", "SellParameter", "TradingResult"]
