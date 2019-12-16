# -*- coding: utf-8 -*-
from sqlalchemy.ext.declarative import declarative_base

from zvdata.contract import register_schema
from zvt.domain.quotes.stock import StockKdataCommon

# kdata schema rule
# 1)name:{entity_type}{level}Kdata
# 2)one db file for one schema

# 股票日k线
Stock1DKdataBase = declarative_base()


class Stock1dKdata(Stock1DKdataBase, StockKdataCommon):
    __tablename__ = 'stock_1d_kdata'


register_schema(providers=['joinquant'], db_name='stock_1d_kdata', schema_base=Stock1DKdataBase)
