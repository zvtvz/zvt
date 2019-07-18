# -*- coding: utf-8 -*-
from sqlalchemy import Column, String, DateTime, Boolean, BigInteger, Float, ForeignKey
from sqlalchemy.orm import relationship

from zvt.domain.common import MetaBase


# 指数和个股为 many to many关系

class StockIndex(MetaBase):
    __tablename__ = 'stock_indices'
    id = Column(String(length=128), primary_key=True)
    timestamp = Column(DateTime)
    stock_id = Column(String(length=128), ForeignKey('stocks.id'), primary_key=True)
    index_id = Column(String(length=128), ForeignKey('indices.id'), primary_key=True)

    indices = relationship("Index", back_populates="stocks")
    stocks = relationship("Stock", back_populates="indices")


# 指数
class Index(MetaBase):
    __tablename__ = 'indices'

    id = Column(String(length=128), primary_key=True)
    timestamp = Column(DateTime)
    exchange = Column(String(length=32))
    type = Column(String(length=64))
    code = Column(String(length=32))
    name = Column(String(length=32))

    is_delisted = Column(Boolean)
    category = Column(String(length=64))

    stocks = relationship('StockIndex', back_populates="indices")

    # 基准点数
    base_point = Column(Float)
    # 发布日期
    online_date = Column(DateTime)

    def __repr__(self):
        return f'[{self.name} - {self.code}]'


# 个股
class Stock(MetaBase):
    __tablename__ = 'stocks'

    id = Column(String(length=128), primary_key=True)
    timestamp = Column(DateTime)
    exchange = Column(String(length=32))
    type = Column(String(length=64))
    code = Column(String(length=32))
    name = Column(String(length=32))

    is_delisted = Column(Boolean)
    industries = Column(String)
    industry_indices = Column(String)
    concept_indices = Column(String)
    area_indices = Column(String)
    indices = relationship('StockIndex', back_populates='stocks')

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
