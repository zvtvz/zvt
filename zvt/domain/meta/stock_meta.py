# -*- coding: utf-8 -*-

from sqlalchemy import Column, String, DateTime, BigInteger, Float
from sqlalchemy.ext.declarative import declarative_base

from zvt.contract import EntityMixin
from zvt.contract.register import register_schema, register_entity
from zvt.utils.time_utils import now_pd_timestamp

StockMetaBase = declarative_base()


class BaseSecurity(EntityMixin):
    # 上市日
    list_date = Column(DateTime)
    # 退市日
    end_date = Column(DateTime)


class BasePortfolio(BaseSecurity):
    @classmethod
    def get_stocks(cls,
                   code=None, codes=None, ids=None, timestamp=now_pd_timestamp(), provider=None):
        """

        :param code: portfolio(etf/block/index...) code
        :param codes: portfolio(etf/block/index...) codes
        :param timestamp:
        :param provider:
        :return:
        """
        portfolio_stock: BasePortfolioStock = eval(f'{cls.__name__}Stock')
        return portfolio_stock.query_data(provider=provider, code=code, codes=codes, ids=ids)


# 个股
@register_entity(entity_type='stock')
class Stock(StockMetaBase, BaseSecurity):
    __tablename__ = 'stock'

# 板块
@register_entity(entity_type='block')
class Block(StockMetaBase, BasePortfolio):
    __tablename__ = 'block'

    # 板块类型，行业(industry),概念(concept)
    category = Column(String(length=64))
    block_type = Column(String(length=64))


# 指数
@register_entity(entity_type='index')
class Index(StockMetaBase, BasePortfolio):
    __tablename__ = 'index'

    # 发布商
    publisher = Column(String(length=64))
    # 类别
    category = Column(String(length=64))
    # 基准点数
    base_point = Column(Float)
    # 基准点数
    base_date = Column(DateTime)

# etf
@register_entity(entity_type='etf')
class Etf(StockMetaBase, BasePortfolio):
    __tablename__ = 'etf'
    category = Column(String(length=64))
    # 主要跟踪标的代码
    underlying_index_code = Column(String(length=64))


    @classmethod
    def get_stocks(cls, code=None, codes=None, ids=None, timestamp=now_pd_timestamp(), provider=None):
        from zvt.api.quote import get_etf_stocks
        return get_etf_stocks(code=code, codes=codes, ids=ids, timestamp=timestamp, provider=provider)


# 基金
@register_entity(entity_type='fund')
class Fund(StockMetaBase, BaseSecurity):
    __tablename__ = 'fund'
    category = Column(String(length=64))


# 组合(Etf,Index,Block)和个股(Stock)的关系 应该继承自该类
# 该基础类可以这样理解:
# entity为组合本身,其包含了stock这种entity,timestamp为持仓日期,从py的"你知道你在干啥"的哲学出发，不加任何约束
class BasePortfolioStock(EntityMixin):
    stock_id = Column(String(length=64))
    stock_code = Column(String(length=64))
    stock_name = Column(String(length=128))


# 支持时间变化,报告期标的调整
class BasePortfolioStockHistory(BasePortfolioStock):
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

class BaseStatus(EntityMixin):
    # 公告日期
    pub_date = Column(DateTime)
    # 变更日期
    change_date = Column(DateTime)
    # 变更原因
    change_reason = Column(String(length=500))
    # 上市状态
    public_status= Column(String(length=32))
    # 变更类型
    change_type= Column(String(length=60))


class BaseName(EntityMixin):
    # 公告日期
    pub_date = Column(DateTime)
    # 变更日期
    change_date = Column(DateTime)
    # 新股票简称
    new_name = Column(String(length=40))
    # 新英文简称
    new_spelling = Column(String(length=40))
    # 原证券简称
    org_name= Column(String(length=40))
    # 原证券英文简称
    org_spelling= Column(String(length=40))

class StockStatus(StockMetaBase, BaseStatus):
    __tablename__ = 'stock_status'


class StockNames(StockMetaBase, BaseName):
    __tablename__ = 'stock_name_change'

class BlockStock(StockMetaBase, BasePortfolioStock):
    __tablename__ = 'block_stock'
    block_type = Column(String(length=40))

class IndexStock(StockMetaBase, BasePortfolioStockHistory):
    __tablename__ = 'index_stock'

class IndexStockNew(StockMetaBase,BasePortfolioStock):
    """
    指数成分股
    """
    __tablename__ = 'index_stock_new'
    # 更新时间
    pub_date = Column(DateTime)
    # 调入时间
    into_date = Column(DateTime)
    # 调出时间
    out_date = Column(DateTime)


class EtfStock(StockMetaBase, BasePortfolioStockHistory):
    __tablename__ = 'etf_stock'

class FundStock(StockMetaBase, BasePortfolioStockHistory):
    __tablename__ = 'fund_stock'

# 个股详情
@register_entity(entity_type='stock_detail')
class StockDetail(StockMetaBase, BaseSecurity):
    __tablename__ = 'stock_detail'

    industries = Column(String(length=64))
    industry_indices = Column(String(length=64))
    concept_indices = Column(String(length=256))
    area_indices = Column(String(length=64))

    # 成立日期
    date_of_establishment = Column(DateTime)
    # 公司简介
    profile = Column(String(length=5000))
    # 主营业务
    main_business = Column(String(length=3000))
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
    # 注册资金
    register_capital = Column(Float)

# 个股详情
class StockDetailNew(StockMetaBase, BaseSecurity):
    __tablename__ = 'stock_detail_new'

    industries = Column(String(length=64))
    industry_indices = Column(String(length=64))
    concept_indices = Column(String(length=256))
    area_indices = Column(String(length=64))

    # 成立日期
    date_of_establishment = Column(DateTime)
    # 公司简介
    profile = Column(String(length=5000))
    # 主营业务
    main_business = Column(String(length=3000))
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
    # 注册资金
    register_capital = Column(Float)

# 场外基金详情
@register_entity(entity_type='fund_detail')
class FundDetail(StockMetaBase, BaseSecurity):
    __tablename__ = 'fund_detail'

    # 基金管理人
    advisor = Column(String(length=100))
    # 基金托管人
    trustee = Column(String(length=100))
    # 基金运作方式编码
    operate_mode_id = Column(BigInteger)
    # 基金运作方式
    operate_mode = Column(String(length=100))
    # 投资标的类型编码
    underlying_asset_type_id = Column(Float)
    # 投资标的类型
    underlying_asset_type = Column(String(length=100))
    # 主要跟踪标的代码
    underlying_index_code = Column(String(length=64))

    category = Column(String(length=64))

register_schema(providers=['joinquant', 'eastmoney', 'exchange', 'sina','emquantapi'], db_name='stock_meta',
                schema_base=StockMetaBase)

__all__ = ['Stock', 'Index', 'Block', 'Etf','Fund','IndexStockNew','StockDetailNew',
           'IndexStock','FundStock', 'BlockStock', 'EtfStock',
           'StockDetail','FundDetail','StockStatus','StockNames']
