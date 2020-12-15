# -*- coding: utf-8 -*-
from sqlalchemy import Column, String, Float
from sqlalchemy.ext.declarative import declarative_base

from zvt.contract import Mixin
from zvt.contract.register import register_schema

OverallBase = declarative_base()


# 市场整体估值

class StockSummary(OverallBase, Mixin):
    __tablename__ = 'stock_summary'

    provider = Column(String(length=32))
    code = Column(String(length=32))
    name = Column(String(length=32))

    total_value = Column(Float)
    total_tradable_vaule = Column(Float)
    pe = Column(Float)
    pb = Column(Float)
    volume = Column(Float)
    turnover = Column(Float)
    turnover_rate = Column(Float)


# 融资融券概况

class MarginTradingSummary(OverallBase, Mixin):
    __tablename__ = 'margin_trading_summary'
    provider = Column(String(length=32))
    code = Column(String(length=32))
    name = Column(String(length=32))

    # 融资余额
    margin_value = Column(Float)
    # 买入额
    margin_buy = Column(Float)

    # 融券余额
    short_value = Column(Float)
    # 卖出量
    short_volume = Column(Float)

    # 融资融券余额
    total_value = Column(Float)


# 北向/南向成交概况

class CrossMarketSummary(OverallBase, Mixin):
    __tablename__ = 'cross_market_summary'
    provider = Column(String(length=32))
    code = Column(String(length=32))
    name = Column(String(length=32))

    buy_amount = Column(Float)
    buy_volume = Column(Float)
    sell_amount = Column(Float)
    sell_volume = Column(Float)
    quota_daily = Column(Float)
    quota_daily_balance = Column(Float)


register_schema(providers=['joinquant', 'exchange'], db_name='overall', schema_base=OverallBase, entity_type='stock')

# the __all__ is generated
__all__ = ['StockSummary', 'MarginTradingSummary', 'CrossMarketSummary']