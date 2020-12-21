# -*- coding: utf-8 -*-
from sqlalchemy import Column, Float, String
from sqlalchemy.ext.declarative import declarative_base

from zvt.contract import Mixin
from zvt.contract.register import register_schema

Stock1dMaFactorBase = declarative_base()


class Stock1dMaFactor(Stock1dMaFactorBase, Mixin):
    __tablename__ = 'Stock1dMaFactor'

    level = Column(String(length=32))
    code = Column(String(length=32))
    name = Column(String(length=32))

    open = Column(Float)
    close = Column(Float)
    high = Column(Float)
    low = Column(Float)

    ma5 = Column(Float)
    ma10 = Column(Float)

    ma34 = Column(Float)
    ma55 = Column(Float)
    ma89 = Column(Float)
    ma144 = Column(Float)

    ma120 = Column(Float)
    ma250 = Column(Float)


register_schema(providers=['zvt'], db_name='stock_1d_ma_factor', schema_base=Stock1dMaFactorBase)
# the __all__ is generated
__all__ = ['Stock1dMaFactor']