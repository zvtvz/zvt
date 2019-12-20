# -*- coding: utf-8 -*-
from sqlalchemy.ext.declarative import declarative_base

from zvdata.contract import register_schema
from zvt.domain.quotes.stock import StockKdataCommon
# 股票30分钟k线
Stock30MKdataBase = declarative_base()


class Stock30mKdata(Stock30MKdataBase, StockKdataCommon):
    __tablename__ = 'stock_30m_kdata'


register_schema(providers=['joinquant'], db_name='stock_30m_kdata', schema_base=Stock30MKdataBase)
