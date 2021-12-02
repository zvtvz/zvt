# -*- coding: utf-8 -*-
from sqlalchemy import Column, String, DateTime, Float, Boolean, Integer
from sqlalchemy.orm import declarative_base

from zvt.contract.register import register_schema
from zvt.contract.schema import TradableMeetActor

StockActorBase = declarative_base()


class StockTopTenFreeHolder(StockActorBase, TradableMeetActor):
    __tablename__ = "stock_top_ten_free_holder"

    report_period = Column(String(length=32))
    report_date = Column(DateTime)

    # 持股数
    holding_numbers = Column(Float)
    # 持股比例
    holding_ratio = Column(Float)
    # 持股市值
    holding_values = Column(Float)


class StockTopTenHolder(StockActorBase, TradableMeetActor):
    __tablename__ = "stock_top_ten_holder"

    report_period = Column(String(length=32))
    report_date = Column(DateTime)

    # 持股数
    holding_numbers = Column(Float)
    # 持股比例
    holding_ratio = Column(Float)
    # 持股市值
    holding_values = Column(Float)


class StockInstitutionalInvestorHolder(StockActorBase, TradableMeetActor):
    __tablename__ = "stock_institutional_investor_holder"

    report_period = Column(String(length=32))
    report_date = Column(DateTime)

    # 持股数
    holding_numbers = Column(Float)
    # 持股比例
    holding_ratio = Column(Float)
    # 持股市值
    holding_values = Column(Float)


class StockActorSummary(StockActorBase, TradableMeetActor):
    __tablename__ = "stock_actor_summary"
    # tradable code
    code = Column(String(length=64))
    # tradable name
    name = Column(String(length=128))

    report_period = Column(String(length=32))
    report_date = Column(DateTime)

    # 变动比例
    change_ratio = Column(Float)
    # 是否完成
    is_complete = Column(Boolean)
    # 持股市值
    actor_type = Column(String)
    actor_count = Column(Integer)

    # 持股数
    holding_numbers = Column(Float)
    # 持股比例
    holding_ratio = Column(Float)
    # 持股市值
    holding_values = Column(Float)


register_schema(providers=["em"], db_name="stock_actor", schema_base=StockActorBase, entity_type="stock")

# the __all__ is generated
__all__ = ["StockTopTenFreeHolder", "StockTopTenHolder", "StockInstitutionalInvestorHolder", "StockActorSummary"]
