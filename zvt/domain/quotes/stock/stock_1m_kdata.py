# -*- coding: utf-8 -*-
from sqlalchemy.ext.declarative import declarative_base

from zvdata.contract import register_schema
from zvt.domain.quotes.stock import StockKdataCommon
# 股票1分钟k线
Stock1mKdataBase = declarative_base()


class Stock1mKdata(Stock1mKdataBase, StockKdataCommon):
    __tablename__ = 'stock_1m_kdata'


register_schema(providers=['joinquant'], db_name='stock_1m_kdata', schema_base=Stock1mKdataBase)
