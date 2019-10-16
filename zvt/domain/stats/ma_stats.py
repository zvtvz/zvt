# -*- coding: utf-8 -*-
from sqlalchemy import Column, String, Float, Integer
from sqlalchemy.ext.declarative import declarative_base

from zvdata import Mixin
from zvt import register_schema

MaStateStatsBase = declarative_base()


class MaStateStats(MaStateStatsBase, Mixin):
    __tablename__ = 'ma_state_stats'

    code = Column(String(length=32))
    name = Column(String(length=32))

    ma5 = Column(Float)
    ma10 = Column(Float)
    score = Column(Float)

    down_current_count = Column(Integer)
    down_current_area = Column(Float)
    down_total_count = Column(Integer)

    up_total_count = Column(Integer)
    up_current_count = Column(Float)
    up_current_area = Column(Integer)


register_schema(providers=['zvt'], db_name='ma_stats', schema_base=MaStateStatsBase)
