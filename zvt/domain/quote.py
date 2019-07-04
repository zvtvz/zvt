# -*- coding: utf-8 -*-
from sqlalchemy import Column, String, DateTime, Float

from zvt.domain.common import Stock1DKdataBase, Index1DKdataBase, Stock1HKdataBase, Stock15MKdataBase, \
    Coin15MKdataBase, Coin1HKdataBase, Coin1DKdataBase, Coin1MKdataBase, Coin5MKdataBase, Coin1WKKdataBase, \
    Stock1MKdataBase, Stock5MKdataBase, Stock30MKdataBase, Stock1WKKdataBase, CoinTickKdataBase


class StockKdataCommon(object):
    id = Column(String(length=128), primary_key=True)
    provider = Column(String(length=32))
    timestamp = Column(DateTime)
    security_id = Column(String(length=128))
    code = Column(String(length=32))
    name = Column(String(length=32))
    # level = Column(Enum(TradingLevel, values_callable=enum_value))
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


class KdataCommon(object):
    id = Column(String(length=128), primary_key=True)
    provider = Column(String(length=32))
    timestamp = Column(DateTime)
    security_id = Column(String(length=128))
    code = Column(String(length=32))
    name = Column(String(length=32))
    level = Column(String(length=32))

    open = Column(Float)
    close = Column(Float)
    high = Column(Float)
    low = Column(Float)
    volume = Column(Float)
    turnover = Column(Float)


class TickCommon(object):
    id = Column(String(length=128), primary_key=True)
    provider = Column(String(length=32))
    timestamp = Column(DateTime)
    security_id = Column(String(length=128))
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
# 1)name:{SecurityType.value.capitalize()}{TradingLevel.value.upper()}Kdata
# 2)one db file for one schema
class Stock1WKKdata(Stock1WKKdataBase, StockKdataCommon):
    __tablename__ = 'stock_1wk_kdata'


class Stock1DKdata(Stock1DKdataBase, StockKdataCommon):
    __tablename__ = 'stock_1d_kdata'


class Stock1HKdata(Stock1HKdataBase, StockKdataCommon):
    __tablename__ = 'stock_1h_kdata'


class Stock30MKdata(Stock30MKdataBase, StockKdataCommon):
    __tablename__ = 'stock_30m_kdata'


class Stock15MKdata(Stock15MKdataBase, StockKdataCommon):
    __tablename__ = 'stock_15m_kdata'


class Stock5MKdata(Stock5MKdataBase, StockKdataCommon):
    __tablename__ = 'stock_5m_kdata'


class Stock1MKdata(Stock1MKdataBase, StockKdataCommon):
    __tablename__ = 'stock_1m_kdata'


class Index1DKdata(Index1DKdataBase, KdataCommon):
    __tablename__ = 'index_1d_kdata'
    turnover_rate = Column(Float)

    # ETF 累计净值（货币 ETF 为七日年化)
    cumulative_net_value = Column(Float)
    # ETF 净值增长率
    change_pct = Column(Float)


class CoinTickKdata(CoinTickKdataBase, TickCommon):
    __tablename__ = 'coin_tick_kdata'


class Coin1MKdata(Coin1MKdataBase, KdataCommon):
    __tablename__ = 'coin_1m_kdata'


class Coin5MKdata(Coin5MKdataBase, KdataCommon):
    __tablename__ = 'coin_5m_kdata'


class Coin15MKdata(Coin15MKdataBase, KdataCommon):
    __tablename__ = 'coin_15m_kdata'


class Coin1HKdata(Coin1HKdataBase, KdataCommon):
    __tablename__ = 'coin_1h_kdata'


class Coin1DKdata(Coin1DKdataBase, KdataCommon):
    __tablename__ = 'coin_1d_kdata'


class Coin1WKKdata(Coin1WKKdataBase, KdataCommon):
    __tablename__ = 'coin_1wk_kdata'
