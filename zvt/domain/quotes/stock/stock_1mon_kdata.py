# -*- coding: utf-8 -*-
from sqlalchemy.ext.declarative import declarative_base

from zvdata.contract import register_schema
from zvt.domain.quotes.stock import StockKdataCommon
# 股票月k线
Stock1monKdataBase = declarative_base()


class Stock1monKdata(Stock1monKdataBase, StockKdataCommon):
    __tablename__ = 'stock_1mon_kdata'


register_schema(providers=['joinquant'], db_name='stock_1mon_kdata', schema_base=Stock1monKdataBase)
