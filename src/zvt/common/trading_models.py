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


class BuyPositionStrategy(BaseModel):
    entity_ids: List[str]
    position_type: PositionType = Field(default=PositionType.normal)
    position_pct: float
    weights: Optional[List[float]] = Field(default=None)


class SellPositionStrategy(BaseModel):
    entity_ids: List[str]
    sell_pcts: Optional[List[float]] = Field(default=None)


class TradingResult(BaseModel):
    success_entity_ids: Optional[List[str]] = Field(default=None)
    failed_entity_ids: Optional[List[str]] = Field(default=None)
