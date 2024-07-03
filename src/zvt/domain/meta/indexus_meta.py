# -*- coding: utf-8 -*-

from sqlalchemy import Column, String, Float
from sqlalchemy.orm import declarative_base

from zvt.contract import Portfolio
from zvt.contract.register import register_schema, register_entity

IndexusMetaBase = declarative_base()


#: 美股指数
@register_entity(entity_type="indexus")
class Indexus(IndexusMetaBase, Portfolio):
    __tablename__ = "index"

    #: 发布商
    publisher = Column(String(length=64))
    #: 类别
    #: see IndexCategory
    category = Column(String(length=64))
    #: 基准点数
    base_point = Column(Float)


register_schema(providers=["em"], db_name="indexus_meta", schema_base=IndexusMetaBase)


# the __all__ is generated
__all__ = ["Indexus"]
