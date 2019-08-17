# -*- coding: utf-8 -*-
from sqlalchemy import Column, String, Float
from sqlalchemy.ext.declarative import declarative_base

from zvdata.domain import register_schema
from zvdata.structs import Mixin


class StockKdataCommon(Mixin):
    provider = Column(String(length=32))
    code = Column(String(length=32))
    name = Column(String(length=32))
    # level = Column(Enum(IntervalLevel, values_callable=enum_value))
    level = Column(String(length=32))

    open = Column(Float)
    hfq_open = Column(Float)
    qfq_open = Column(Float)
    close = Column(Float)
    hfq_close = Column(Float)
    qfq_close = Column(Float)
    high = Column(Float)
    hfq_high = Column(Float)
    qfq_high = Column(Float)
    low = Column(Float)
    hfq_low = Column(Float)
    qfq_low = Column(Float)
    volume = Column(Float)
    turnover = Column(Float)
    change_pct = Column(Float)
    turnover_rate = Column(Float)
    factor = Column(Float)


class KdataCommon(Mixin):
    provider = Column(String(length=32))
    code = Column(String(length=32))
    name = Column(String(length=32))
    level = Column(String(length=32))

    open = Column(Float)
    close = Column(Float)
    high = Column(Float)
    low = Column(Float)
    volume = Column(Float)
    turnover = Column(Float)


class TickCommon(Mixin):
    provider = Column(String(length=32))
    code = Column(String(length=32))
    name = Column(String(length=32))
    level = Column(String(length=32))

    order = Column(String(length=32))
    price = Column(Float)
    volume = Column(Float)
    turnover = Column(Float)
    direction = Column(String(length=32))
    orderType = Column(String(length=32))


# kdata schema rule
# 1)name:{entity_type}{level}Kdata
# 2)one db file for one schema


Stock1mKdataBase = declarative_base()


class Stock1mKdata(Stock1mKdataBase, StockKdataCommon):
    __tablename__ = 'stock_1m_kdata'


register_schema(providers=['joinquant'], db_name='stock_1m_kdata', schema_base=Stock1mKdataBase)

Stock5MKdataBase = declarative_base()


class Stock5mKdata(Stock5MKdataBase, StockKdataCommon):
    __tablename__ = 'stock_5m_kdata'


register_schema(providers=['joinquant'], db_name='stock_5m_kdata', schema_base=Stock5MKdataBase)

Stock15MKdataBase = declarative_base()


class Stock15mKdata(Stock15MKdataBase, StockKdataCommon):
    __tablename__ = 'stock_15m_kdata'


Stock30MKdataBase = declarative_base()


class Stock30mKdata(Stock30MKdataBase, StockKdataCommon):
    __tablename__ = 'stock_30m_kdata'


Stock1HKdataBase = declarative_base()


class Stock1hKdata(Stock1HKdataBase, StockKdataCommon):
    __tablename__ = 'stock_1h_kdata'


register_schema(providers=['joinquant'], db_name='stock_1h_kdata', schema_base=Stock1HKdataBase)

Stock1DKdataBase = declarative_base()


class Stock1dKdata(Stock1DKdataBase, StockKdataCommon):
    __tablename__ = 'stock_1d_kdata'


register_schema(providers=['joinquant', 'netease'], db_name='stock_1d_kdata', schema_base=Stock1DKdataBase)

Stock1WKKdataBase = declarative_base()


class Stock1wkKdata(Stock1WKKdataBase, StockKdataCommon):
    __tablename__ = 'stock_1wk_kdata'


register_schema(providers=['joinquant', 'netease'], db_name='stock_1wk_kdata', schema_base=Stock1WKKdataBase)

Index1DKdataBase = declarative_base()


class Index1dKdata(Index1DKdataBase, KdataCommon):
    __tablename__ = 'index_1d_kdata'
    turnover_rate = Column(Float)

    # ETF 累计净值（货币 ETF 为七日年化)
    cumulative_net_value = Column(Float)
    # ETF 净值增长率
    change_pct = Column(Float)


register_schema(providers=['exchange'], db_name='index_1d_kdata', schema_base=Index1DKdataBase)

CoinTickKdataBase = declarative_base()


class CoinTickKdata(CoinTickKdataBase, TickCommon):
    __tablename__ = 'coin_tick_kdata'


register_schema(providers=['ccxt'], db_name='coin_tick_kdata', schema_base=CoinTickKdataBase)

Coin1mKdataBase = declarative_base()


class Coin1mKdata(Coin1mKdataBase, KdataCommon):
    __tablename__ = 'coin_1m_kdata'


register_schema(providers=['ccxt'], db_name='coin_1m_kdata', schema_base=Coin1mKdataBase)

Coin5MKdataBase = declarative_base()


class Coin5mKdata(Coin5MKdataBase, KdataCommon):
    __tablename__ = 'coin_5m_kdata'


register_schema(providers=['ccxt'], db_name='coin_5m_kdata', schema_base=Coin5MKdataBase)

Coin15MKdataBase = declarative_base()


class Coin15mKdata(Coin15MKdataBase, KdataCommon):
    __tablename__ = 'coin_15m_kdata'


register_schema(providers=['ccxt'], db_name='coin_15m_kdata', schema_base=Coin15MKdataBase)

Coin1HKdataBase = declarative_base()


class Coin1hKdata(Coin1HKdataBase, KdataCommon):
    __tablename__ = 'coin_1h_kdata'


register_schema(providers=['ccxt'], db_name='coin_1h_kdata', schema_base=Coin1HKdataBase)

Coin1DKdataBase = declarative_base()


class Coin1dKdata(Coin1DKdataBase, KdataCommon):
    __tablename__ = 'coin_1d_kdata'


register_schema(providers=['ccxt'], db_name='coin_1d_kdata', schema_base=Coin1DKdataBase)

Coin1WKKdataBase = declarative_base()


class Coin1wkKdata(Coin1WKKdataBase, KdataCommon):
    __tablename__ = 'coin_1wk_kdata'


register_schema(providers=['ccxt'], db_name='coin_1wk_kdata', schema_base=Coin1WKKdataBase)
