# -*- coding: utf-8 -*-
from sqlalchemy import Column, String, DateTime, Enum, Float

from zvt.domain.common import TradingLevel, StockKdataBase, Provider, enum_value


class StockKdata(StockKdataBase):
    __tablename__ = 'stock_kdata'

    id = Column(String(length=128), primary_key=True)
    provider = Column(Enum(Provider, values_callable=enum_value), primary_key=True)
    timestamp = Column(DateTime)
    security_id = Column(String(length=128))
    code = Column(String(length=32))
    name = Column(String(length=32))
    level = Column(Enum(TradingLevel, values_callable=enum_value))

    open = Column(Float)
    hfq_open = Column(Float)
    qfq_open = Column(Float)
    close = Column(Float)
    hfq_close = Column(Float)
    qfq_close = Column(Float)
    high = Column(Float)
    hfq_high = Column(Float)
    qfq_high = Column(Float)
    low = Column(Float)
    hfq_low = Column(Float)
    qfq_low = Column(Float)
    volume = Column(Float)
    turnover = Column(Float)
    change_pct = Column(Float)
    turnover_rate = Column(Float)
    factor = Column(Float)


class IndexKdata(StockKdataBase):
    __tablename__ = 'index_kdata'

    id = Column(String(length=128), primary_key=True)
    provider = Column(Enum(Provider, values_callable=enum_value), primary_key=True)
    timestamp = Column(DateTime)
    security_id = Column(String(length=128))
    code = Column(String(length=32))
    name = Column(String(length=32))
    level = Column(Enum(TradingLevel, values_callable=enum_value))

    open = Column(Float)
    close = Column(Float)
    high = Column(Float)
    low = Column(Float)
    volume = Column(Float)
    turnover = Column(Float)
    turnover_rate = Column(Float)
