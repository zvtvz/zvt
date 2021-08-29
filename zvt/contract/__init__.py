# -*- coding: utf-8 -*-
from enum import Enum


class IntervalLevel(Enum):
    LEVEL_TICK = 'tick'
    LEVEL_1MIN = '1m'
    LEVEL_5MIN = '5m'
    LEVEL_15MIN = '15m'
    LEVEL_30MIN = '30m'
    LEVEL_1HOUR = '1h'
    LEVEL_4HOUR = '4h'
    LEVEL_1DAY = '1d'
    LEVEL_1WEEK = '1wk'
    LEVEL_1MON = '1mon'

    def to_pd_freq(self):
        if self == IntervalLevel.LEVEL_1MIN:
            return '1min'
        if self == IntervalLevel.LEVEL_5MIN:
            return '5min'
        if self == IntervalLevel.LEVEL_15MIN:
            return '15min'
        if self == IntervalLevel.LEVEL_30MIN:
            return '30min'
        if self == IntervalLevel.LEVEL_1HOUR:
            return '1H'
        if self == IntervalLevel.LEVEL_4HOUR:
            return '4H'
        if self >= IntervalLevel.LEVEL_1DAY:
            return '1D'

    def floor_timestamp(self, pd_timestamp):
        if self == IntervalLevel.LEVEL_1MIN:
            return pd_timestamp.floor('1min')
        if self == IntervalLevel.LEVEL_5MIN:
            return pd_timestamp.floor('5min')
        if self == IntervalLevel.LEVEL_15MIN:
            return pd_timestamp.floor('15min')
        if self == IntervalLevel.LEVEL_30MIN:
            return pd_timestamp.floor('30min')
        if self == IntervalLevel.LEVEL_1HOUR:
            return pd_timestamp.floor('1h')
        if self == IntervalLevel.LEVEL_4HOUR:
            return pd_timestamp.floor('4h')
        if self == IntervalLevel.LEVEL_1DAY:
            return pd_timestamp.floor('1d')

    def to_minute(self):
        return int(self.to_second() / 60)

    def to_second(self):
        return int(self.to_ms() / 1000)

    def to_ms(self):
        # we treat tick intervals is 5s, you could change it
        if self == IntervalLevel.LEVEL_TICK:
            return 5 * 1000
        if self == IntervalLevel.LEVEL_1MIN:
            return 60 * 1000
        if self == IntervalLevel.LEVEL_5MIN:
            return 5 * 60 * 1000
        if self == IntervalLevel.LEVEL_15MIN:
            return 15 * 60 * 1000
        if self == IntervalLevel.LEVEL_30MIN:
            return 30 * 60 * 1000
        if self == IntervalLevel.LEVEL_1HOUR:
            return 60 * 60 * 1000
        if self == IntervalLevel.LEVEL_4HOUR:
            return 4 * 60 * 60 * 1000
        if self == IntervalLevel.LEVEL_1DAY:
            return 24 * 60 * 60 * 1000
        if self == IntervalLevel.LEVEL_1WEEK:
            return 7 * 24 * 60 * 60 * 1000
        if self == IntervalLevel.LEVEL_1MON:
            return 31 * 7 * 24 * 60 * 60 * 1000

    def __ge__(self, other):
        if self.__class__ is other.__class__:
            return self.to_ms() >= other.to_ms()
        return NotImplemented

    def __gt__(self, other):

        if self.__class__ is other.__class__:
            return self.to_ms() > other.to_ms()
        return NotImplemented

    def __le__(self, other):
        if self.__class__ is other.__class__:
            return self.to_ms() <= other.to_ms()
        return NotImplemented

    def __lt__(self, other):
        if self.__class__ is other.__class__:
            return self.to_ms() < other.to_ms()
        return NotImplemented


class AdjustType(Enum):
    # 这里用拼音，因为英文不直观 split-adjusted？wtf?
    # 不复权
    bfq = 'bfq'
    # 前复权
    qfq = 'qfq'
    # 后复权
    hfq = 'hfq'


class ActorType(Enum):
    # 个人
    individual = 'individual'
    # 公募基金
    raised_fund = 'raised_fund'
    # 社保
    social_security = 'social_security'
    # 保险
    insurance = 'insurance'
    # 外资
    qfii = 'qfii'
    # 信托
    trust = 'trust'
    # 券商
    broker = 'broker'
    # 私募
    private_equity = 'private_equity'
    # 公司(可能包括私募)
    corporation = 'corporation'


class TradableType(Enum):
    # A股(中国)
    stock = 'stock'
    # 美股
    stockus = 'stockus'
    # 港股
    stockhk = 'stockhk'
    # 期货(中国)
    future = 'future'
    # 数字货币
    coin = 'coin'
    # 期权
    option = 'option'
    # 基金
    fund = 'fund'


class Exchange(Enum):
    # 上证交易所
    sh = 'sh'
    # 深证交易所
    sz = 'sz'

    # 对于中国的非交易所的 标的
    cn = 'cn'

    # 纳斯达克
    nasdaq = 'nasdaq'

    # 纽交所
    nyse = 'nyse'

    # 港交所
    hk = 'hk'

    # 数字货币
    binance = 'binance'
    huobipro = 'huobipro'

    # 上海期货交易所
    shfe = 'shfe'
    # 大连商品交易所
    dce = "dce"
    # 郑州商品交易所
    czce = 'czce'
    # 中国金融期货交易所
    cffex = 'cffex'


from . import zvt_context
from .schema import Mixin, NormalMixin, TradableEntity, NormalEntityMixin, PortfolioStock, Portfolio, \
    PortfolioStockHistory

__all__ = ['IntervalLevel', 'Mixin', 'NormalMixin', 'TradableEntity', 'NormalEntityMixin', 'zvt_context', 'AdjustType',
           'Portfolio', 'PortfolioStock', 'PortfolioStockHistory']
