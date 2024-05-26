# -*- coding: utf-8 -*-
from sqlalchemy import Column, String, DateTime, Boolean, Float, Integer, ForeignKey, func, JSON
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import relationship

from zvt.contract import Mixin
from zvt.contract.register import register_schema
from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, relationship

TradingBase = declarative_base()


class TradingPlan(TradingBase, Mixin):
    __tablename__ = "trading_plan"
    stock_id = Column(String)
    stock_code = Column(String)
    stock_name = Column(String)
    trading_date = Column(DateTime)
    # 预期开盘涨跌幅
    expected_open_pct = Column(Float, nullable=False)
    buy_price = Column(Float)
    sell_price = Column(Float)
    # 操作理由
    trading_reason = Column(String)
    # 交易信号
    trading_signal_type = Column(String)
    # 执行状态
    status = Column(String)
    # 复盘
    review = Column(String)


class QueryStockQuoteSetting(TradingBase, Mixin):
    __tablename__ = "query_stock_quote_setting"
    stock_pool_name = Column(String)
    main_tags = Column(JSON)


register_schema(providers=["zvt"], db_name="stock_trading", schema_base=TradingBase)
