# -*- coding: utf-8 -*-

from sqlalchemy import Column, String
from sqlalchemy.orm import declarative_base

from zvt.contract import Portfolio, PortfolioStockHistory
from zvt.contract.register import register_schema, register_entity
from zvt.utils.time_utils import now_pd_timestamp

EtfMetaBase = declarative_base()


# etf
@register_entity(entity_type='etf')
class Etf(EtfMetaBase, Portfolio):
    __tablename__ = 'etf'
    category = Column(String(length=64))

    @classmethod
    def get_stocks(cls, code=None, codes=None, ids=None, timestamp=now_pd_timestamp(), provider=None):
        from zvt.api.portfolio import get_etf_stocks
        return get_etf_stocks(code=code, codes=codes, ids=ids, timestamp=timestamp, provider=provider)


class EtfStock(EtfMetaBase, PortfolioStockHistory):
    __tablename__ = 'etf_stock'


register_schema(providers=['exchange','joinquant'], db_name='etf_meta', schema_base=EtfMetaBase)
# the __all__ is generated
__all__ = ['Etf', 'EtfStock']