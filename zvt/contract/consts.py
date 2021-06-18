# -*- coding: utf-8 -*-
from enum import Enum


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
    stock = 'stock'
    future = 'future'
    coin = 'coin'
    option = 'option'
    fund = 'fund'


class Exchange(Enum):
    # 上证交易所
    sh = 'sh'
    # 深证交易所
    sz = 'sz'

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
