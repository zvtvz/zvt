# -*- coding: utf-8 -*-
from sqlalchemy import Column, String, Float
from sqlalchemy.ext.declarative import declarative_base

from zvdata.contract import register_schema, register_api
from zvdata import Mixin

MacroBase = declarative_base()


# 市场整体估值
@register_api(provider='joinquant')
class StockSummary(MacroBase, Mixin):
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
@register_api(provider='joinquant')
class MarginTradingSummary(MacroBase, Mixin):
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
@register_api(provider='joinquant')
class CrossMarketSummary(MacroBase, Mixin):
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


register_schema(providers=['exchange', 'joinquant'], db_name='macro', schema_base=MacroBase)
