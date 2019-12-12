# -*- coding: utf-8 -*-
from sqlalchemy import Column, String, DateTime, Boolean, BigInteger, Float, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from zvdata import EntityMixin
from zvdata.contract import register_schema, register_api, register_entity

StockMetaBase = declarative_base()


# 指数和个股为 many to many关系
class StockIndex(StockMetaBase):
    __tablename__ = 'stock_index'
    id = Column(String(length=128), primary_key=True)
    timestamp = Column(DateTime)
    stock_id = Column(String(length=128), ForeignKey('stock.id'), primary_key=True)
    index_id = Column(String(length=128), ForeignKey('index.id'), primary_key=True)

    indices = relationship("Index", back_populates="stocks")
    stocks = relationship("Stock", back_populates="indices")


# 指数
@register_api(provider='exchange')
@register_entity(entity_type='index')
class Index(StockMetaBase, EntityMixin):
    __tablename__ = 'index'

    is_delisted = Column(Boolean)
    category = Column(String(length=64))

    stocks = relationship('StockIndex', back_populates="indices")

    # 基准点数
    base_point = Column(Float)
    # 发布日期
    list_date = Column(DateTime)

    def __repr__(self):
        return f'[{self.name} - {self.code}]'


# 个股
@register_api(provider='eastmoney')
@register_entity(entity_type='stock')
class Stock(StockMetaBase, EntityMixin):
    __tablename__ = 'stock'

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


register_schema(providers=['eastmoney', 'exchange', 'sina'], db_name='stock_meta', schema_base=StockMetaBase)
