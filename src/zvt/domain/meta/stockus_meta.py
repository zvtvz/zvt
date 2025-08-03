# -*- coding: utf-8 -*-
import pytz
from sqlalchemy import Column, Float, String
from sqlalchemy.orm import declarative_base

from zvt.contract import TradableEntity
from zvt.contract.register import register_schema, register_entity

StockusMetaBase = declarative_base()


#: 美股
@register_entity(entity_type="stockus")
class Stockus(StockusMetaBase, TradableEntity):
    __tablename__ = "stockus"

    #: 流通市值
    float_cap = Column(Float)
    #: 总市值
    total_cap = Column(Float)
    #: 所属行业
    industry = Column(String)

    @classmethod
    def get_timezone(cls):
        return pytz.timezone("America/New_York")

    @classmethod
    def get_trading_t(cls):
        """
        0 means t+0
        1 means t+1

        :return:
        """
        return 0

    @classmethod
    def get_trading_intervals(cls, include_bidding_time=False):
        """
        overwrite it to get the trading intervals of the entity

        :return: list of time intervals, in format [(start,end)]
        """
        return [("09:30", "16:00")]


register_schema(providers=["em"], db_name="stockus_meta", schema_base=StockusMetaBase)


# the __all__ is generated
__all__ = ["Stockus"]
