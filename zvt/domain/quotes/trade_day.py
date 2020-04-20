# -*- coding: utf-8 -*-
from sqlalchemy.ext.declarative import declarative_base

from zvt.core import Mixin
from zvt.core.contract import register_api, register_schema

TradeDayBase = declarative_base()


@register_api(provider='joinquant')
class StockTradeDay(TradeDayBase, Mixin):
    __tablename__ = 'stock_trade_day'


register_schema(providers=['joinquant'], db_name='trade_day', schema_base=TradeDayBase)

__all__ = ['StockTradeDay']
