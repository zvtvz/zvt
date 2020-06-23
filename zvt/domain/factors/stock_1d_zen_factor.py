# -*- coding: utf-8 -*-
import enum

from sqlalchemy import Column, Float, String
from sqlalchemy.ext.declarative import declarative_base

from zvt.contract import Mixin
from zvt.contract.register import register_schema

Stock1dZenFactorBase = declarative_base()


# k线的状态
class KState(enum.Enum):
    # 上升k线，可转换为 顶分型
    up = 'up'
    # 下降k线，可转换为 底分型
    down = 'down'

    # 顶分型
    ding = 'ding'
    # 底分型
    di = 'di'


# 笔的状态
class BiState(enum.Enum):
    # 向上笔，底分型 连 顶分型
    up = 'up'
    # 向下笔，顶分型 连 底分型
    down = 'down'


# 中枢状态
class ZenState(enum.Enum):
    # 震荡
    shaking = 'shaking'
    # 趋势向上
    up = 'up'
    # 趋势向下
    down = 'down'


class Stock1dZenFactor(Stock1dZenFactorBase, Mixin):
    __tablename__ = 'Stock1dZenFactor'

    level = Column(String(length=32))
    code = Column(String(length=32))
    name = Column(String(length=32))

    open = Column(Float)
    close = Column(Float)
    high = Column(Float)
    low = Column(Float)

    # KState，当下k线的状态是确定的，笔状态的 延续和打破 受其影响
    k_state = Column(String(length=32))
    # BiState
    bi_state = Column(String(length=32))
    # ZenState
    zen_state = Column(String(length=32))


register_schema(providers=['zvt'], db_name='stock_1d_zen_factor', schema_base=Stock1dZenFactorBase)
