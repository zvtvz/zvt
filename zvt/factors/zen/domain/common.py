# -*- coding: utf-8 -*-
from sqlalchemy import Column, Float, String, Boolean

from zvt.contract import Mixin


class ZenFactorCommon(Mixin):
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

    # 笔的底
    bi_di = Column(Boolean)
    # 笔的顶
    bi_ding = Column(Boolean)
    # 记录笔顶/底分型的值，bi_di取low,bi_ding取high,其他为None,绘图时取有值的连线即为 笔
    bi_value = Column(Float)

    # 记录临时分型，不变
    tmp_ding = Column(Boolean)
    tmp_di = Column(Boolean)

    duan_state = Column(String(length=32))

    # 段的底
    duan_di = Column(Boolean)
    # 段的顶
    duan_ding = Column(Boolean)
    # 记录段顶/底的值，为duan_di时取low,为duan_ding时取high,其他为None,绘图时取有值的连线即为 段
    duan_value = Column(Float)

    # 记录在确定中枢的最后一个段的终点x1，值为Rect(x0,y0,x1,y1)
    zhongshu = Column(String(length=512))
# the __all__ is generated
__all__ = ['ZenFactorCommon']