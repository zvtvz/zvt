# -*- coding: utf-8 -*-
from sqlalchemy.ext.declarative import declarative_base

from zvdata.contract import register_schema
from zvt.domain.quotes.stock import StockKdataCommon
# 股票1小时k线
Stock1HKdataBase = declarative_base()


class Stock1hKdata(Stock1HKdataBase, StockKdataCommon):
    __tablename__ = 'stock_1h_kdata'


register_schema(providers=['joinquant'], db_name='stock_1h_kdata', schema_base=Stock1HKdataBase)
