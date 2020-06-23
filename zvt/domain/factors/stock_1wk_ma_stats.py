# -*- coding: utf-8 -*-
from sqlalchemy import Column, Float, Integer, String
from sqlalchemy.ext.declarative import declarative_base

from zvt.contract import Mixin
from zvt.contract.register import register_schema

Stock1wkMaStateStatsBase = declarative_base()


class Stock1wkMaStateStats(Stock1wkMaStateStatsBase, Mixin):
    __tablename__ = 'stock_1wk_ma_state_stats'

    level = Column(String(length=32))
    ma5 = Column(Float)
    ma10 = Column(Float)
    score = Column(Float)

    current_count = Column(Integer)
    total_count = Column(Integer)


register_schema(providers=['zvt'], db_name='stock_1wk_ma_stats', schema_base=Stock1wkMaStateStatsBase)
