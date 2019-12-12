# -*- coding: utf-8 -*-
from sqlalchemy import String, Column, Float

from zvdata import Mixin


class KdataCommon(Mixin):
    provider = Column(String(length=32))
    code = Column(String(length=32))
    name = Column(String(length=32))
    # Enum constraint is not extendable
    # level = Column(Enum(IntervalLevel, values_callable=enum_value))
    level = Column(String(length=32))

    # 如果是股票，代表前复权数据
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


class StockKdataCommon(KdataCommon):
    # 涨跌幅
    change_pct = Column(Float)
    # 换手率
    turnover_rate = Column(Float)

    def fetch_data(self, recorder_index: int = 0, entity_ids=None, codes=None, batch_size=10, force_update=False,
                   sleeping_time=5, default_size=2000, real_time=False, fix_duplicate_way='add', start_timestamp=None,
                   end_timestamp=None, close_hour=15, close_minute=30):
        cls = self.__class__
        if hasattr(cls, 'recorders') and cls.recorders:
            recorder_class = cls.recorders[recorder_index]
            print(f'{cls.__name__} registered recorders:{cls.recorders}')

            from zvdata.recorder import FixedCycleDataRecorder
            # FixedCycleDataRecorder
            if issubclass(recorder_class, FixedCycleDataRecorder):
                table: str = self.__class__.__tablename__
                level = table.split('_')[1]
                r = recorder_class(entity_ids=entity_ids, codes=codes, batch_size=batch_size, force_update=force_update,
                                   sleeping_time=sleeping_time, default_size=default_size, real_time=real_time,
                                   fix_duplicate_way=fix_duplicate_way, start_timestamp=start_timestamp,
                                   end_timestamp=end_timestamp, close_hour=close_hour, close_minute=close_minute,
                                   level=level)
                r.run()
                return
        else:
            print(f'no recorders for {cls.__name__}')


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
