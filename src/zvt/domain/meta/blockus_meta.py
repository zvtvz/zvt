# -*- coding: utf-8 -*-

from sqlalchemy import Column, String
from sqlalchemy.orm import declarative_base

from zvt.contract import Portfolio, PortfolioStock
from zvt.contract.register import register_schema, register_entity

BlockusMetaBase = declarative_base()


#: 板块
@register_entity(entity_type="blockus")
class Blockus(BlockusMetaBase, Portfolio):
    __tablename__ = "block"

    #: 板块类型，行业(industry),概念(concept)
    category = Column(String(length=64))


class BlockusStockus(BlockusMetaBase, PortfolioStock):
    __tablename__ = "blockus_stockus"


register_schema(providers=["em"], db_name="blockus_meta", schema_base=BlockusMetaBase)


# the __all__ is generated
__all__ = ["Blockus", "BlockusStockus"]
