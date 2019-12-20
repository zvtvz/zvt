# -*- coding: utf-8 -*-
from sqlalchemy.ext.declarative import declarative_base

from zvdata.contract import register_schema
from zvt.domain.quotes.stock import StockKdataCommon
# 股票5分钟k线
Stock5MKdataBase = declarative_base()


class Stock5mKdata(Stock5MKdataBase, StockKdataCommon):
    __tablename__ = 'stock_5m_kdata'


register_schema(providers=['joinquant'], db_name='stock_5m_kdata', schema_base=Stock5MKdataBase)
