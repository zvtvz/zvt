# -*- coding: utf-8 -*-
from enum import Enum


class IntervalLevel(Enum):
    """
    Repeated fixed time interval, e.g, 5m, 1d.
    """

    #: level l2 quote
    LEVEL_L2_QUOTE = "l2quote"
    #: level tick
    LEVEL_TICK = "tick"
    #: 1 minute
    LEVEL_1MIN = "1m"
    #: 5 minutes
    LEVEL_5MIN = "5m"
    #: 15 minutes
    LEVEL_15MIN = "15m"
    #: 30 minutes
    LEVEL_30MIN = "30m"
    #: 1 hour
    LEVEL_1HOUR = "1h"
    #: 4 hours
    LEVEL_4HOUR = "4h"
    #: 1 day
    LEVEL_1DAY = "1d"
    #: 1 week
    LEVEL_1WEEK = "1wk"
    #: 1 month
    LEVEL_1MON = "1mon"

    def to_pd_freq(self):
        if self == IntervalLevel.LEVEL_1MIN:
            return "1min"
        if self == IntervalLevel.LEVEL_5MIN:
            return "5min"
        if self == IntervalLevel.LEVEL_15MIN:
            return "15min"
        if self == IntervalLevel.LEVEL_30MIN:
            return "30min"
        if self == IntervalLevel.LEVEL_1HOUR:
            return "1H"
        if self == IntervalLevel.LEVEL_4HOUR:
            return "4H"
        if self >= IntervalLevel.LEVEL_1DAY:
            return "1D"

    def floor_timestamp(self, pd_timestamp):
        if self == IntervalLevel.LEVEL_1MIN:
            return pd_timestamp.floor("1min")
        if self == IntervalLevel.LEVEL_5MIN:
            return pd_timestamp.floor("5min")
        if self == IntervalLevel.LEVEL_15MIN:
            return pd_timestamp.floor("15min")
        if self == IntervalLevel.LEVEL_30MIN:
            return pd_timestamp.floor("30min")
        if self == IntervalLevel.LEVEL_1HOUR:
            return pd_timestamp.floor("1h")
        if self == IntervalLevel.LEVEL_4HOUR:
            return pd_timestamp.floor("4h")
        if self == IntervalLevel.LEVEL_1DAY:
            return pd_timestamp.floor("1d")

    def to_minute(self):
        return int(self.to_second() / 60)

    def to_second(self):
        return int(self.to_ms() / 1000)

    def to_ms(self):
        """
        To seconds count in the interval

        :return: seconds count in the interval
        """
        #: we treat tick intervals is 5s, you could change it
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
    """
    split-adjusted type for :class:`~.zvt.contract.schema.TradableEntity` quotes

    """

    #: not adjusted
    #: 不复权
    bfq = "bfq"
    #: pre adjusted
    #: 前复权
    qfq = "qfq"
    #: post adjusted
    #: 后复权
    hfq = "hfq"


class ActorType(Enum):
    #: 个人
    individual = "individual"
    #: 公募基金
    raised_fund = "raised_fund"
    #: 社保
    social_security = "social_security"
    #: 保险
    insurance = "insurance"
    #: 外资
    qfii = "qfii"
    #: 信托
    trust = "trust"
    #: 券商
    broker = "qmt"
    #: 私募
    private_equity = "private_equity"
    #: 公司(可能包括私募)
    corporation = "corporation"


class TradableType(Enum):
    #: A股(中国)
    #: China stock
    stock = "stock"
    #: 可转债(中国)
    #: China convertible Bond
    cbond = "cbond"
    #: A股指数(中国)
    #: China index
    index = "index"
    #: A股板块(中国)
    #: China stock block
    block = "block"
    #: 美股
    #: USA stock
    stockus = "stockus"
    #: 美股指数
    #: USA index
    indexus = "indexus"
    #: 港股
    #: Hongkong Stock
    stockhk = "stockhk"
    #: 期货(中国)
    #: China future
    future = "future"
    #: 数字货币
    #: Cryptocurrency
    coin = "coin"
    #: 期权(中国)
    #: China option
    option = "option"
    #: 基金(中国)
    #: China fund
    fund = "fund"
    #: 货币汇率
    #: currency exchange rate
    currency = "currency"


class Exchange(Enum):
    #: 上证交易所
    sh = "sh"
    #: 深证交易所
    sz = "sz"
    #: 北交所
    bj = "bj"

    #: 对于中国的非交易所的 标的
    cn = "cn"
    #: 对于美国的非交易所的 标的
    us = "us"

    #: 纳斯达克
    nasdaq = "nasdaq"

    #: 纽交所
    nyse = "nyse"

    #: 港交所
    hk = "hk"

    #: 数字货币
    binance = "binance"
    huobipro = "huobipro"

    #: 上海期货交易所
    shfe = "shfe"
    #: 大连商品交易所
    dce = "dce"
    #: 郑州商品交易所
    czce = "czce"
    #: 中国金融期货交易所
    cffex = "cffex"
    #: 上海国际能源交易中心
    ine = "ine"

    #: 外汇交易所(虚拟)
    #: currency exchange(virtual)
    forex = "forex"
    #: 人民币中间价


tradable_type_map_exchanges = {
    TradableType.block: [Exchange.cn],
    TradableType.index: [Exchange.sh, Exchange.sz],
    TradableType.stock: [Exchange.sh, Exchange.sz, Exchange.bj],
    TradableType.cbond: [Exchange.sh, Exchange.sz],
    TradableType.stockhk: [Exchange.hk],
    TradableType.stockus: [Exchange.nasdaq, Exchange.nyse],
    TradableType.indexus: [Exchange.us],
    TradableType.future: [Exchange.shfe, Exchange.dce, Exchange.czce, Exchange.cffex, Exchange.ine],
    TradableType.coin: [Exchange.binance, Exchange.huobipro],
    TradableType.currency: [Exchange.forex],
}


def get_entity_exchanges(entity_type):
    entity_type = TradableType(entity_type)
    return tradable_type_map_exchanges.get(entity_type)


from .context import zvt_context

zvt_context = zvt_context


# the __all__ is generated
__all__ = ["IntervalLevel", "AdjustType", "ActorType", "TradableType", "Exchange", "get_entity_exchanges"]

# __init__.py structure:
# common code of the package
# export interface in __all__ which contains __all__ of its sub modules

# import all from submodule schema
from .schema import *
from .schema import __all__ as _schema_all

__all__ += _schema_all
