# -*- coding: utf-8 -*-
from sqlalchemy.ext.declarative import declarative_base

from zvt.contract import Mixin
from zvt.contract.register import register_schema

TradeDayBase = declarative_base()


class StockTradeDay(TradeDayBase, Mixin):
    __tablename__ = 'stock_trade_day'


register_schema(providers=['joinquant'], db_name='trade_day', schema_base=TradeDayBase)

__all__ = ['StockTradeDay']
# the __all__ is generated
__all__ = ['StockTradeDay']