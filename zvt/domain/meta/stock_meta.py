# -*- coding: utf-8 -*-

from sqlalchemy import Column, String, DateTime, BigInteger, Float
from sqlalchemy.ext.declarative import declarative_base

from zvt.contract import EntityMixin
from zvt.contract.register import register_schema, register_entity
from zvt.contract import Portfolio, PortfolioStock, PortfolioStockHistory
from zvt.utils.time_utils import now_pd_timestamp

StockMetaBase = declarative_base()


# 个股
@register_entity(entity_type='stock')
class Stock(StockMetaBase, EntityMixin):
    __tablename__ = 'stock'


# 板块
@register_entity(entity_type='block')
class Block(StockMetaBase, Portfolio):
    __tablename__ = 'block'

    # 板块类型，行业(industry),概念(concept)
    category = Column(String(length=64))


# 指数
@register_entity(entity_type='index')
class Index(StockMetaBase, Portfolio):
    __tablename__ = 'index'

    # 发布商
    publisher = Column(String(length=64))
    # 类别
    category = Column(String(length=64))
    # 基准点数
    base_point = Column(Float)


# etf
@register_entity(entity_type='etf')
class Etf(StockMetaBase, Portfolio):
    __tablename__ = 'etf'
    category = Column(String(length=64))

    @classmethod
    def get_stocks(cls, code=None, codes=None, ids=None, timestamp=now_pd_timestamp(), provider=None):
        from zvt.api.quote import get_etf_stocks
        return get_etf_stocks(code=code, codes=codes, ids=ids, timestamp=timestamp, provider=provider)


class BlockStock(StockMetaBase, PortfolioStock):
    __tablename__ = 'block_stock'


class IndexStock(StockMetaBase, PortfolioStockHistory):
    __tablename__ = 'index_stock'


class EtfStock(StockMetaBase, PortfolioStockHistory):
    __tablename__ = 'etf_stock'


# 个股详情
@register_entity(entity_type='stock_detail')
class StockDetail(StockMetaBase, EntityMixin):
    __tablename__ = 'stock_detail'

    industries = Column(String)
    industry_indices = Column(String)
    concept_indices = Column(String)
    area_indices = Column(String)

    # 成立日期
    date_of_establishment = Column(DateTime)
    # 公司简介
    profile = Column(String(length=1024))
    # 主营业务
    main_business = Column(String(length=512))
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


register_schema(providers=['joinquant', 'eastmoney', 'exchange', 'sina'], db_name='stock_meta',
                schema_base=StockMetaBase)

# the __all__ is generated
__all__ = ['Stock', 'Block', 'Index', 'Etf', 'BlockStock', 'IndexStock', 'EtfStock', 'StockDetail']