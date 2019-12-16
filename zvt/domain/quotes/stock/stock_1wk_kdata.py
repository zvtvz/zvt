# -*- coding: utf-8 -*-
from sqlalchemy.ext.declarative import declarative_base

from zvdata.contract import register_schema
from zvt.domain.quotes.stock import StockKdataCommon
# 股票周k线
Stock1wkKdataBase = declarative_base()


class Stock1wkKdata(Stock1wkKdataBase, StockKdataCommon):
    __tablename__ = 'stock_1wk_kdata'


register_schema(providers=['joinquant'], db_name='stock_1wk_kdata', schema_base=Stock1wkKdataBase)
