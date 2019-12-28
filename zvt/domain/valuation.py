# -*- coding: utf-8 -*-
from sqlalchemy import Column, String, Float
from sqlalchemy.ext.declarative import declarative_base

from zvdata import Mixin
from zvdata.contract import register_api, register_schema

ValuationBase = declarative_base()


@register_api(provider='joinquant')
class Valuation(ValuationBase, Mixin):
    __tablename__ = 'valuation'

    code = Column(String(length=32))
    name = Column(String(length=32))

    # 市值
    market_cap = Column(Float)
    # 流通市值
    circulating_market_cap = Column(Float)
    # 换手率
    turnover_ratio = Column(Float)
    # 静态pe
    pe = Column(Float)
    # 动态pe
    pe_ttm = Column(Float)
    # 市净率
    pb = Column(Float)
    # 市销率
    ps = Column(Float)
    # 市现率
    pcf = Column(Float)


register_schema(providers=['joinquant'], db_name='valuation', schema_base=ValuationBase)
