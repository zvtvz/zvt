# -*- coding: utf-8 -*-
from sqlalchemy import Column, Float, String, Boolean, Integer
from sqlalchemy.ext.declarative import declarative_base

from zvdata import Mixin
from zvdata.contract import register_schema

Stock1dZenFactorBase = declarative_base()


class Stock1dZenFactor(Stock1dZenFactorBase, Mixin):
    __tablename__ = 'Stock1dZenFactor'

    level = Column(String(length=32))
    code = Column(String(length=32))
    name = Column(String(length=32))

    open = Column(Float)
    close = Column(Float)
    high = Column(Float)
    low = Column(Float)

    # 确定的顶分型
    zen_ding = Column(Boolean)
    # 未确定的顶
    tmp_ding = Column(Boolean)
    # 确定的底分型
    zen_di = Column(Boolean)
    # 未确定的底
    tmp_di = Column(Boolean)

    # 笔的状态，1代表向上，-1代表向下
    zen_bi_state = Column(Integer)
    tmp_bi_state = Column(Integer)


register_schema(providers=['zvt'], db_name='stock_1d_zen_factor', schema_base=Stock1dZenFactorBase)
