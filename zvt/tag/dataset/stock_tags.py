# -*- coding: utf-8 -*-
from sqlalchemy import Column, String
from sqlalchemy.orm import declarative_base

from zvt.contract import Mixin
from zvt.contract.register import register_schema

StockTagsBase = declarative_base()


class StockTags(StockTagsBase, Mixin):
    __tablename__ = "stock_tags"

    actor_tag = Column(String(length=64))
    style_tag = Column(String(length=64))
    cycle_tag = Column(String(length=64))
    market_value_tag = Column(String(length=64))


register_schema(providers=["zvt"], db_name="stock_tags", schema_base=StockTagsBase)
# the __all__ is generated
__all__ = ["StockTags"]
