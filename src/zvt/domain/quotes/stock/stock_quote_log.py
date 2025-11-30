# -*- coding: utf-8 -*-
from sqlalchemy import Column, Float, Integer, Boolean
from sqlalchemy.orm import declarative_base

from zvt.contract.register import register_schema
from zvt.domain.quotes import StockKdataCommon

StockQuoteLogBase = declarative_base()


class StockQuoteLog(StockQuoteLogBase, StockKdataCommon):
    __tablename__ = "stock_quote_log"
    #: UNIX时间戳
    time = Column(Integer)
    #: 最新价
    price = Column(Float)
    #: 冲涨停
    near_limit_up = Column(Boolean)
    #: 封涨停金额
    # limit_up_amount = Column(Float)
    #: 封跌停金额
    # limit_down_amount = Column(Float)
    #: 5挡卖单金额
    # ask_amount = Column(Float)
    #: 5挡买单金额
    # bid_amount = Column(Float)
    #: 流通市值
    float_cap = Column(Float)
    #: 总市值
    total_cap = Column(Float)


register_schema(providers=["qmt"], db_name="stock_quote_log", schema_base=StockQuoteLogBase, entity_type="stock")


# the __all__ is generated
__all__ = ["StockQuoteLog"]
