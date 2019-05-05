# -*- coding: utf-8 -*-
from sqlalchemy import Column, String, DateTime, Float

from zvt.domain.common import StockDayKdataBase, IndexDayKdataBase


class StockDayKdata(StockDayKdataBase):
    __tablename__ = 'stock_day_kdata'

    id = Column(String(length=128), primary_key=True)
    provider = Column(String(length=32))
    timestamp = Column(DateTime)
    security_id = Column(String(length=128))
    code = Column(String(length=32))
    name = Column(String(length=32))
    # level = Column(Enum(TradingLevel, values_callable=enum_value))
    level = Column(String(length=32))

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


class IndexDayKdata(IndexDayKdataBase):
    __tablename__ = 'index_day_kdata'

    id = Column(String(length=128), primary_key=True)
    provider = Column(String(length=32))
    timestamp = Column(DateTime)
    security_id = Column(String(length=128))
    code = Column(String(length=32))
    name = Column(String(length=32))
    # level = Column(Enum(TradingLevel, values_callable=enum_value))
    level = Column(String(length=32))

    open = Column(Float)
    close = Column(Float)
    high = Column(Float)
    low = Column(Float)
    volume = Column(Float)
    turnover = Column(Float)
    turnover_rate = Column(Float)
