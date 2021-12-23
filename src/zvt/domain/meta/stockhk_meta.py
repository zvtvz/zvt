# -*- coding: utf-8 -*-
from sqlalchemy import Column, Boolean
from sqlalchemy.orm import declarative_base

from zvt.contract import TradableEntity
from zvt.contract.register import register_schema, register_entity

StockhkMetaBase = declarative_base()


# 港股
@register_entity(entity_type="stockhk")
class Stockhk(StockhkMetaBase, TradableEntity):
    __tablename__ = "stockhk"
    # 是否属于港股通
    south = Column(Boolean)


register_schema(providers=["em"], db_name="stockhk_meta", schema_base=StockhkMetaBase)
# the __all__ is generated
__all__ = ["Stockhk"]
