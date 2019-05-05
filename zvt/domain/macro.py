# -*- coding: utf-8 -*-
from sqlalchemy import Column, String, DateTime, Enum, Float

from zvt.domain.common import Provider, enum_value, MacroBase


class GDP(MacroBase):
    __tablename__ = 'gdp'

    id = Column(String(length=128), primary_key=True)
    provider = Column(String(length=32))
    timestamp = Column(DateTime)
    security_id = Column(String(length=128))
    code = Column(String(length=32))
    name = Column(String(length=32))

    value = Column(Float)


class StockSummary(MacroBase):
    __tablename__ = 'stock_summary'

    id = Column(String(length=128), primary_key=True)
    provider = Column(String(length=32))
    timestamp = Column(DateTime)
    security_id = Column(String(length=128))
    code = Column(String(length=32))
    name = Column(String(length=32))

    total_value = Column(Float)
    total_tradable_vaule = Column(Float)
    pe = Column(Float)
    volume = Column(Float)
    turnover = Column(Float)
    turnover_rate = Column(Float)
