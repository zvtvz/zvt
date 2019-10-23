# -*- coding: utf-8 -*-
from sqlalchemy.ext.declarative import declarative_base

from zvdata.contract import register_schema
from zvt.domain.quotes import KdataCommon

Coin1monKdataBase = declarative_base()


class Coin1monKdata(Coin1monKdataBase, KdataCommon):
    __tablename__ = 'coin_1mon_kdata'


register_schema(providers=['ccxt'], db_name='coin_1mon_kdata', schema_base=Coin1monKdataBase)
