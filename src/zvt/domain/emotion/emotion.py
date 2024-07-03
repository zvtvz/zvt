# -*- coding: utf-8 -*-
from sqlalchemy import Column, String, Integer, DateTime, Boolean, Float
from sqlalchemy.orm import declarative_base

from zvt.contract import Mixin
from zvt.contract.register import register_schema

EmotionBase = declarative_base()


class LimitUpInfo(EmotionBase, Mixin):
    __tablename__ = "limit_up_info"

    code = Column(String(length=32))
    name = Column(String(length=32))
    #: 是否新股
    is_new = Column(Boolean)
    #: 是否回封，是就是打开过，否相反
    is_again_limit = Column(Boolean)
    #: 涨停打开次数,0代表封住就没开板
    open_count = Column(Integer)
    #: 首次封板时间
    first_limit_up_time = Column(DateTime)
    #: 最后封板时间
    last_limit_up_time = Column(DateTime)
    #: 涨停类型:换手板，一字板
    limit_up_type = Column(String)
    #: 封单金额
    order_amount = Column(String)
    #: 最近一年封板成功率
    success_rate = Column(Float)
    #: 流通市值
    currency_value = Column(Float)
    #: 涨幅
    change_pct = Column(Float)
    #: 换手率
    turnover_rate = Column(Float)
    #: 涨停原因
    reason = Column(String)
    #: 几天几板
    high_days = Column(String)
    #: 最近几板，不一定是连板
    high_days_count = Column(Integer)


class LimitDownInfo(EmotionBase, Mixin):
    __tablename__ = "limit_down_info"

    code = Column(String(length=32))
    name = Column(String(length=32))
    #: 是否新股
    is_new = Column(Boolean)
    #: 是否回封，是就是打开过，否相反
    is_again_limit = Column(Boolean)
    #: 流通市值
    currency_value = Column(Float)
    #: 涨幅
    change_pct = Column(Float)
    #: 换手率
    turnover_rate = Column(Float)


class Emotion(EmotionBase, Mixin):
    __tablename__ = "emotion"
    #: 涨停数量
    limit_up_count = Column(Integer)
    #: 炸板数
    limit_up_open_count = Column(Integer)
    #: 涨停封板成功率
    limit_up_success_rate = Column(Float)

    #: 连板高度
    max_height = Column(Integer)
    #: 连板数x个数 相加
    continuous_power = Column(Integer)

    #: 跌停数量
    limit_down_count = Column(Integer)
    #: 跌停打开
    limit_down_open_count = Column(Integer)
    #: 跌停封板成功率
    limit_down_success_rate = Column(Float)


register_schema(providers=["jqka"], db_name="emotion", schema_base=EmotionBase)


# the __all__ is generated
__all__ = ["LimitUpInfo", "LimitDownInfo", "Emotion"]
