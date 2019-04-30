# -*- coding: utf-8 -*-
from sqlalchemy import Column, String, DateTime, Boolean, Enum, BigInteger, Float, Table, ForeignKey
from sqlalchemy.orm import mapper, relationship

from zvt.domain.common import MetaBase, SecurityType, StockCategory, \
    Provider, enum_value

# 指数和个股为 many to many关系
stock_indices = Table('stock_indices', MetaBase.metadata,
                      Column('stock_id', ForeignKey('stocks.id'), primary_key=True),
                      Column('index_id', ForeignKey('indices.id'), primary_key=True),
                      Column('provider', Enum(Provider, values_callable=enum_value), primary_key=True)
                      )


class StockIndex(object):
    def __init__(self, stock_id, index_id, provider) -> None:
        self.stock_id = stock_id
        self.index_id = index_id
        self.provider = provider


mapper(StockIndex, stock_indices)


# 指数
class Index(MetaBase):
    __tablename__ = 'indices'

    id = Column(String(length=128), primary_key=True)
    provider = Column(Enum(Provider, values_callable=enum_value), primary_key=True)
    timestamp = Column(DateTime)
    exchange = Column(String(length=32))
    type = Column(Enum(SecurityType, values_callable=enum_value))
    code = Column(String(length=32))
    name = Column(String(length=32))

    is_delisted = Column(Boolean)
    category = Column(Enum(StockCategory, values_callable=enum_value))

    stocks = relationship("Stock", secondary=stock_indices, back_populates="indices")


# 个股
class Stock(MetaBase):
    __tablename__ = 'stocks'

    id = Column(String(length=128), primary_key=True)
    provider = Column(Enum(Provider, values_callable=enum_value), primary_key=True)
    timestamp = Column(DateTime)
    exchange = Column(String(length=32))
    type = Column(Enum(SecurityType, values_callable=enum_value))
    code = Column(String(length=32))
    name = Column(String(length=32))

    is_delisted = Column(Boolean)
    industries = Column(String)
    industry_indices = Column(String)
    concept_indices = Column(String)
    area_indices = Column(String)
    indices = relationship("Index", secondary=stock_indices, back_populates='stocks')

    # 成立日期
    date_of_establishment = Column(DateTime)
    # 公司简介
    profile = Column(String(length=1024))
    # 主营业务
    main_business = Column(String(length=512))
    # 上市日期
    list_date = Column(DateTime)
    # 发行量(股)
    issues = Column(BigInteger)
    # 发行价格
    price = Column(Float)
    # 募资净额(元)
    raising_fund = Column(Float)
    # 发行市盈率
    issue_pe = Column(Float)
    # 网上中签率
    net_winning_rate = Column(Float)
