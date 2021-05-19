# -*- coding: utf-8 -*-
from enum import Enum


class PlayerType(Enum):
    # 个人
    individual = 'individual'
    # 基金
    fund = 'fund'
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
    # 公司(包括私募)
    corporation = 'corporation'


class EntityType(Enum):
    stock = 'stock'
    future = 'future'
    coin = 'coin'
    option = 'option'


class Exchange(Enum):
    sh = 'sh'
    sz = 'sz'
