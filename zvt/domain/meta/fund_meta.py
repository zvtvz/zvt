# -*- coding: utf-8 -*-
from sqlalchemy import Column, String, Integer
from sqlalchemy.ext.declarative import declarative_base

from zvt.contract import Portfolio, PortfolioStockHistory
from zvt.contract.register import register_entity, register_schema
from zvt.utils import now_pd_timestamp

FundMetaBase = declarative_base()


# 个股
@register_entity(entity_type='fund')
class Fund(FundMetaBase, Portfolio):
    __tablename__ = 'fund'
    # 基金管理人
    advisor = Column(String(length=100))
    # 基金托管人
    trustee = Column(String(length=100))

    # 编码	基金运作方式
    # 401001	开放式基金
    # 401002	封闭式基金
    # 401003	QDII
    # 401004	FOF
    # 401005	ETF
    # 401006	LOF
    # 基金运作方式编码
    operate_mode_id = Column(Integer)
    # 基金运作方式
    operate_mode = Column(String(length=32))

    # 编码	基金类别
    # 402001	股票型
    # 402002	货币型
    # 402003	债券型
    # 402004	混合型
    # 402005	基金型
    # 402006	贵金属
    # 402007	封闭式
    # 投资标的类型编码
    underlying_asset_type_id = Column(Integer)
    # 投资标的类型
    underlying_asset_type = Column(String(length=32))

    @classmethod
    def get_stocks(cls, code=None, codes=None, ids=None, timestamp=now_pd_timestamp(), provider=None):
        from zvt.api.quote import get_fund_stocks
        return get_fund_stocks(code=code, codes=codes, ids=ids, timestamp=timestamp, provider=provider)


class FundStock(FundMetaBase, PortfolioStockHistory):
    __tablename__ = 'fund_stock'


register_schema(providers=['joinquant'], db_name='fund_meta', schema_base=FundMetaBase)
# the __all__ is generated
__all__ = ['Fund', 'FundStock']
