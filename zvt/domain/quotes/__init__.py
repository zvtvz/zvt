# -*- coding: utf-8 -*-
from sqlalchemy import String, Column, Float

from zvdata import Mixin


class StockKdataCommon(Mixin):
    provider = Column(String(length=32))
    code = Column(String(length=32))
    name = Column(String(length=32))
    # Enum constraint is not extendable
    # level = Column(Enum(IntervalLevel, values_callable=enum_value))
    level = Column(String(length=32))

    open = Column(Float)
    hfq_open = Column(Float)
    qfq_open = Column(Float)
    close = Column(Float)
    hfq_close = Column(Float)
    qfq_close = Column(Float)
    high = Column(Float)
    hfq_high = Column(Float)
    qfq_high = Column(Float)
    low = Column(Float)
    hfq_low = Column(Float)
    qfq_low = Column(Float)
    volume = Column(Float)
    turnover = Column(Float)
    change_pct = Column(Float)
    turnover_rate = Column(Float)
    factor = Column(Float)


class KdataCommon(Mixin):
    provider = Column(String(length=32))
    code = Column(String(length=32))
    name = Column(String(length=32))
    level = Column(String(length=32))

    open = Column(Float)
    close = Column(Float)
    high = Column(Float)
    low = Column(Float)
    volume = Column(Float)
    turnover = Column(Float)


class TickCommon(Mixin):
    provider = Column(String(length=32))
    code = Column(String(length=32))
    name = Column(String(length=32))
    level = Column(String(length=32))

    order = Column(String(length=32))
    price = Column(Float)
    volume = Column(Float)
    turnover = Column(Float)
    direction = Column(String(length=32))
    order_type = Column(String(length=32))


from .coin_tick_kdata import *
from .coin_1m_kdata import *
from .coin_1h_kdata import *
from .coin_1d_kdata import *
from .coin_1wk_kdata import *
from .coin_1mon_kdata import *

from .index_1d_kdata import *
from .index_1wk_kdata import *
from .index_1mon_kdata import *

from .stock_1m_kdata import *
from .stock_5m_kdata import *
from .stock_15m_kdata import *
from .stock_30m_kdata import *
from .stock_1h_kdata import *
from .stock_1d_kdata import *
from .stock_1wk_kdata import *
from .stock_1mon_kdata import *
