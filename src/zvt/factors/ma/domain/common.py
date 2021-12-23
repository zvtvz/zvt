# -*- coding: utf-8 -*-
from sqlalchemy import Column, Float, Integer

from zvt.contract import Mixin


class MaStatsFactorCommon(Mixin):
    open = Column(Float)
    close = Column(Float)
    high = Column(Float)
    low = Column(Float)
    turnover = Column(Float)

    ma5 = Column(Float)
    ma10 = Column(Float)

    ma34 = Column(Float)
    ma55 = Column(Float)
    ma89 = Column(Float)
    ma144 = Column(Float)

    ma120 = Column(Float)
    ma250 = Column(Float)

    vol_ma30 = Column(Float)

    live = Column(Integer)
    count = Column(Integer)
    distance = Column(Float)
    area = Column(Float)


# the __all__ is generated
__all__ = ["MaStatsFactorCommon"]
