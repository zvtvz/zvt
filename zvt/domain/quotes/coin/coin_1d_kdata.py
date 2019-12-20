# -*- coding: utf-8 -*-
from sqlalchemy.ext.declarative import declarative_base

from zvdata.contract import register_schema
from zvt.domain.quotes.coin import CoinKdataCommon

Coin1dKdataBase = declarative_base()


class Coin1dKdata(Coin1dKdataBase, CoinKdataCommon):
    __tablename__ = 'coin_1d_kdata'


register_schema(providers=['ccxt'], db_name='coin_1d_kdata', schema_base=Coin1dKdataBase)
