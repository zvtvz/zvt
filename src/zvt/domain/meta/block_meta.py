# -*- coding: utf-8 -*-

from sqlalchemy import Column, String
from sqlalchemy.orm import declarative_base

from zvt.contract import Portfolio, PortfolioStock
from zvt.contract.register import register_schema, register_entity

BlockMetaBase = declarative_base()


#: 板块
@register_entity(entity_type="block")
class Block(BlockMetaBase, Portfolio):
    __tablename__ = "block"

    #: 板块类型，行业(industry),概念(concept)
    category = Column(String(length=64))


class BlockStock(BlockMetaBase, PortfolioStock):
    __tablename__ = "block_stock"


register_schema(providers=["em", "eastmoney", "sina"], db_name="block_meta", schema_base=BlockMetaBase)
# the __all__ is generated
__all__ = ["Block", "BlockStock"]
