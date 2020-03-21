# -*- coding: utf-8 -*-
from sqlalchemy import Column, Float, Integer, String
from sqlalchemy.ext.declarative import declarative_base

from zvdata import Mixin
from zvdata.contract import register_schema

Stock1dMaStateStatsBase = declarative_base()


class Stock1dMaStateStats(Stock1dMaStateStatsBase, Mixin):
    __tablename__ = 'stock_1d_ma_state_stats'

    level = Column(String(length=32))
    ma5 = Column(Float)
    ma10 = Column(Float)
    score = Column(Float)

    # 维持状态的次数
    current_count = Column(Integer)
    # 涨跌幅
    current_pct = Column(Integer)

    # 此轮维持状态的最大值，即切换点
    total_count = Column(Integer)
    # 涨跌幅
    # total_pct = Column(Integer)


register_schema(providers=['zvt'], db_name='stock_1d_ma_stats', schema_base=Stock1dMaStateStatsBase)
