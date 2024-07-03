# -*- coding: utf-8 -*-
from sqlalchemy import String, Column, Float, Integer, Boolean
from sqlalchemy.orm import declarative_base

from zvt.contract import Mixin
from zvt.contract.register import register_schema

StockQuoteBase = declarative_base()


class StockQuote(StockQuoteBase, Mixin):
    __tablename__ = "stock_quote"
    code = Column(String(length=32))
    name = Column(String(length=32))

    #: UNIX时间戳
    time = Column(Integer)
    #: 最新价
    price = Column(Float)
    # 涨跌幅
    change_pct = Column(Float)
    # 成交金额
    turnover = Column(Float)
    # 换手率
    turnover_rate = Column(Float)
    #: 是否涨停
    is_limit_up = Column(Boolean)
    #: 封涨停金额
    limit_up_amount = Column(Float)
    #: 是否跌停
    is_limit_down = Column(Boolean)
    #: 封跌停金额
    limit_down_amount = Column(Float)
    #: 5挡卖单金额
    ask_amount = Column(Float)
    #: 5挡买单金额
    bid_amount = Column(Float)
    #: 流通市值
    float_cap = Column(Float)
    #: 总市值
    total_cap = Column(Float)


register_schema(providers=["qmt"], db_name="stock_quote", schema_base=StockQuoteBase, entity_type="stock")


# the __all__ is generated
__all__ = ["StockQuote"]
