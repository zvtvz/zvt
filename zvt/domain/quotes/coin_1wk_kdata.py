# -*- coding: utf-8 -*-
from sqlalchemy.ext.declarative import declarative_base

from zvdata.contract import register_schema
from zvt.domain.quotes import KdataCommon

Coin1wkKdataBase = declarative_base()


class Coin1wkKdata(Coin1wkKdataBase, KdataCommon):
    __tablename__ = 'coin_1wk_kdata'


register_schema(providers=['ccxt'], db_name='coin_1wk_kdata', schema_base=Coin1wkKdataBase)
