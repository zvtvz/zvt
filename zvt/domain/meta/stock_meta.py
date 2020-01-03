# -*- coding: utf-8 -*-
from sqlalchemy import Column, String, DateTime, Boolean, BigInteger, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

from zvdata import EntityMixin
from zvdata.contract import register_schema, register_entity

StockMetaBase = declarative_base()


class BaseSecurity(EntityMixin):
    # 是否退市
    is_delisted = Column(Boolean)
    # 上市日
    list_date = Column(DateTime)


# 个股
@register_entity(entity_type='stock')
class Stock(StockMetaBase, BaseSecurity):
    __tablename__ = 'stock'


# 板块
class Block(StockMetaBase, BaseSecurity):
    __tablename__ = 'block'

    # 板块类型，行业(industry),概念(concept)
    category = Column(String(length=64))


# 指数
@register_entity(entity_type='index')
class Index(StockMetaBase, BaseSecurity):
    __tablename__ = 'index'

    # 发布商
    publisher = Column(String(length=64))
    # 类别
    category = Column(String(length=64))
    # 基准点数
    base_point = Column(Float)


# etf
@register_entity(entity_type='etf')
class Etf(StockMetaBase, BaseSecurity):
    __tablename__ = 'etf'
    category = Column(String(length=64))


# 组合(Etf,Index,Block)和个股(Stock)的关系 应该继承自该类
# 该基础类可以这样理解:
# 其是一种包含关系，即本身是entity,但包含了stock这种entity,timestamp为持仓日期,从py的"你知道你在干啥"的哲学出发，不加任何约束
class BasePortfolio(EntityMixin):
    stock_id = Column(String)
    stock_code = Column(String(length=64))
    stock_name = Column(String(length=128))


# 支持时间变化,报告期标的调整
class Portfolio(BasePortfolio):
    # 报告期,season1,half_year,season3,year
    report_period = Column(String(length=32))
    # 3-31,6-30,9-30,12-31
    report_date = Column(DateTime)

    # 占净值比例
    proportion = Column(Float)
    # 持有股票的数量
    shares = Column(Float)
    # 持有股票的市值
    market_cap = Column(Float)


class BlockStock(StockMetaBase, BasePortfolio):
    __tablename__ = 'block_stock'


class IndexStock(StockMetaBase, BasePortfolio):
    __tablename__ = 'index_stock'


class EtfStock(StockMetaBase, Portfolio):
    __tablename__ = 'etf_stock'


# 个股详情
@register_entity(entity_type='stock_detail')
class StockDetail(StockMetaBase, EntityMixin):
    __tablename__ = 'stock_detail'

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


register_schema(providers=['eastmoney', 'exchange', 'sina', 'joinquant'], db_name='stock_meta',
                schema_base=StockMetaBase)
