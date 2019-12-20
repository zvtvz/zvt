# -*- coding: utf-8 -*-
from sqlalchemy.ext.declarative import declarative_base

# 数字货币tick
from zvdata.contract import register_schema
from zvt.domain.quotes.coin import CoinTickCommon

CoinTickKdataBase = declarative_base()


class CoinTickKdata(CoinTickKdataBase, CoinTickCommon):
    __tablename__ = 'coin_tick_kdata'


register_schema(providers=['ccxt'], db_name='coin_tick_kdata', schema_base=CoinTickKdataBase)
