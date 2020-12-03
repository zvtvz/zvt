# -*- coding: utf-8 -*-
from sqlalchemy import String, Column, Float

from zvt.contract import Mixin


class KdataCommon(Mixin):
    provider = Column(String(length=32))
    code = Column(String(length=32))
    name = Column(String(length=32))
    # Enum constraint is not extendable
    # level = Column(Enum(IntervalLevel, values_callable=enum_value))
    level = Column(String(length=32))

    # 开盘价
    open = Column(Float)
    # 收盘价
    close = Column(Float)
    # 最高价
    high = Column(Float)
    # 最低价
    low = Column(Float)
    # 成交量
    volume = Column(Float)
    # 成交金额
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


class BlockKdataCommon(KdataCommon):
    pass


class IndexKdataCommon(KdataCommon):
    pass


class EtfKdataCommon(KdataCommon):
    turnover_rate = Column(Float)

    # ETF 累计净值（货币 ETF 为七日年化)
    cumulative_net_value = Column(Float)
    # ETF 净值增长率
    change_pct = Column(Float)


class StockKdataCommon(KdataCommon):
    # 涨跌幅
    change_pct = Column(Float)
    # 换手率
    turnover_rate = Column(Float)


# the __all__ is generated
__all__ = ['KdataCommon', 'TickCommon', 'BlockKdataCommon', 'IndexKdataCommon', 'EtfKdataCommon', 'StockKdataCommon']

# __init__.py structure:
# common code of the package
# export interface in __all__ which contains __all__ of its sub modules

# import all from submodule trade_day
from .trade_day import *
from .trade_day import __all__ as _trade_day_all
__all__ += _trade_day_all

# import all from submodule common
from .common import *
from .common import __all__ as _common_all
__all__ += _common_all

# import all from submodule index
from .index import *
from .index import __all__ as _index_all
__all__ += _index_all

# import all from submodule etf
from .etf import *
from .etf import __all__ as _etf_all
__all__ += _etf_all

# import all from submodule stock
from .stock import *
from .stock import __all__ as _stock_all
__all__ += _stock_all

# import all from submodule block
from .block import *
from .block import __all__ as _block_all
__all__ += _block_all