# -*- coding: utf-8 -*-
from sqlalchemy import String, Column, Float, Integer, JSON

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
    # 涨跌幅
    change_pct = Column(Float)
    # 换手率
    turnover_rate = Column(Float)


class TickCommon(Mixin):
    #: UNIX时间戳
    time = Column(Integer)
    #: 开盘价
    open = Column(Float)
    #: 收盘价/当前价格
    close = Column(Float)
    #: 最高价
    high = Column(Float)
    #: 最低价
    low = Column(Float)
    #: 成交量
    volume = Column(Float)
    #: 成交金额
    turnover = Column(Float)
    #: 委卖价
    ask_price = Column(Float)
    #: 委买价
    bid_price = Column(Float)
    #: 委卖量
    ask_vol = Column(JSON)
    #: 委买量
    bid_vol = Column(JSON)
    #: 成交笔数
    transaction_num = Column(Integer)


class BlockKdataCommon(KdataCommon):
    pass


class IndexKdataCommon(KdataCommon):
    pass


class IndexusKdataCommon(KdataCommon):
    pass


class EtfKdataCommon(KdataCommon):
    turnover_rate = Column(Float)

    # ETF 累计净值（货币 ETF 为七日年化)
    cumulative_net_value = Column(Float)


class StockKdataCommon(KdataCommon):
    pass


class StockusKdataCommon(KdataCommon):
    pass


class StockhkKdataCommon(KdataCommon):
    pass


# future common kdata
class FutureKdataCommon(KdataCommon):
    #: 持仓量
    interest = Column(Float)
    #: 结算价
    settlement = Column(Float)
    #: 涨跌幅(按收盘价)
    # change_pct = Column(Float)
    #: 涨跌幅(按结算价)
    change_pct1 = Column(Float)


class CurrencyKdataCommon(KdataCommon):
    #: 持仓量
    interest = Column(Float)
    #: 结算价
    settlement = Column(Float)
    #: 涨跌幅(按收盘价)
    # change_pct = Column(Float)
    #: 涨跌幅(按结算价)
    change_pct1 = Column(Float)


# the __all__ is generated
__all__ = [
    "KdataCommon",
    "TickCommon",
    "BlockKdataCommon",
    "IndexKdataCommon",
    "IndexusKdataCommon",
    "EtfKdataCommon",
    "StockKdataCommon",
    "StockusKdataCommon",
    "StockhkKdataCommon",
    "FutureKdataCommon",
    "CurrencyKdataCommon",
]

# __init__.py structure:
# common code of the package
# export interface in __all__ which contains __all__ of its sub modules

# import all from submodule trade_day
from .trade_day import *
from .trade_day import __all__ as _trade_day_all

__all__ += _trade_day_all

# import all from submodule indexus
from .indexus import *
from .indexus import __all__ as _indexus_all

__all__ += _indexus_all

# import all from submodule stockhk
from .stockhk import *
from .stockhk import __all__ as _stockhk_all

__all__ += _stockhk_all

# import all from submodule stockus
from .stockus import *
from .stockus import __all__ as _stockus_all

__all__ += _stockus_all

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

# import all from submodule currency
from .currency import *
from .currency import __all__ as _currency_all

__all__ += _currency_all

# import all from submodule future
from .future import *
from .future import __all__ as _future_all

__all__ += _future_all

# import all from submodule block
from .block import *
from .block import __all__ as _block_all

__all__ += _block_all
