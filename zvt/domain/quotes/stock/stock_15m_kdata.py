# -*- coding: utf-8 -*-
from sqlalchemy.ext.declarative import declarative_base

from zvdata.contract import register_schema
from zvt.domain.quotes.stock import StockKdataCommon
# 股票15分钟k线
Stock15MKdataBase = declarative_base()


class Stock15mKdata(Stock15MKdataBase, StockKdataCommon):
    __tablename__ = 'stock_15m_kdata'


register_schema(providers=['joinquant'], db_name='stock_15m_kdata', schema_base=Stock15MKdataBase)
