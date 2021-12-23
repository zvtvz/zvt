# -*- coding: utf-8 -*-

from sqlalchemy.orm import declarative_base

from zvt.contract import TradableEntity
from zvt.contract.register import register_schema, register_entity

StockusMetaBase = declarative_base()


# 美股
@register_entity(entity_type="stockus")
class Stockus(StockusMetaBase, TradableEntity):
    __tablename__ = "stockus"


register_schema(providers=["em"], db_name="stockus_meta", schema_base=StockusMetaBase)
# the __all__ is generated
__all__ = ["Stockus"]
