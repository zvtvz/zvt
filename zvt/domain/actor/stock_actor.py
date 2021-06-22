# -*- coding: utf-8 -*-
from sqlalchemy import Column, String, DateTime, Float
from sqlalchemy.orm import declarative_base

from zvt.contract.register import register_schema
from zvt.contract.schema import TradableMeetActor

StockActorBase = declarative_base()


class StockTopTenTradableHolder(StockActorBase, TradableMeetActor):
    __tablename__ = 'stock_top_ten_tradable_holder'

    report_period = Column(String(length=32))
    report_date = Column(DateTime)

    # 持股数
    holding_numbers = Column(Float)
    # 持股比例
    holding_ratio = Column(Float)
    # 变动
    change = Column(Float)
    # 变动比例
    change_ratio = Column(Float)


class StockTopTenHolder(StockActorBase, TradableMeetActor):
    __tablename__ = 'stock_top_ten_holder'

    report_period = Column(String(length=32))
    report_date = Column(DateTime)

    # 持股数
    holding_numbers = Column(Float)
    # 持股比例
    holding_ratio = Column(Float)
    # 变动
    change = Column(Float)
    # 变动比例
    change_ratio = Column(Float)


class StockInstitutionalInvestorHolder(StockActorBase, TradableMeetActor):
    __tablename__ = 'stock_institutional_investor_holder'

    report_period = Column(String(length=32))
    report_date = Column(DateTime)

    # 持股数
    holding_numbers = Column(Float)
    # 持股比例
    holding_ratio = Column(Float)
    # 持股市值
    holding_values = Column(Float)


register_schema(providers=['em'], db_name='stock_actor', schema_base=StockActorBase, entity_type='stock')

# the __all__ is generated
__all__ = ['StockTopTenTradableHolder', 'StockTopTenHolder', 'StockInstitutionalInvestorHolder']
