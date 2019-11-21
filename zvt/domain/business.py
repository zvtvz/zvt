# -*- coding: utf-8 -*-
from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, Float, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

# business data
from zvdata.contract import register_schema

BusinessBase = declarative_base()


class Trader(BusinessBase):
    __tablename__ = 'trader'
    id = Column(String(length=128), primary_key=True)
    # 时间
    timestamp = Column(DateTime)
    # 机器人名字
    trader_name = Column(String(length=128))

    entity_ids = Column(String(length=1024))
    entity_type = Column(String(length=128))
    exchanges = Column(String(length=128))
    codes = Column(String(length=128))
    start_timestamp = Column(DateTime)
    end_timestamp = Column(DateTime)
    provider = Column(String(length=32))
    level = Column(String(length=32))
    real_time = Column(Boolean)
    kdata_use_begin_time = Column(Boolean)
    # TODO:inspect selector/factors
    # selectors = Column(String(length=1024))
    # factors = Column(String(length=1024))
    # technical_factors = Column(String(length=1024))


# 一天只有一条记录
class SimAccount(BusinessBase):
    __tablename__ = 'sim_account'

    id = Column(String(length=128), primary_key=True)
    # 时间
    timestamp = Column(DateTime)

    # 机器人名字
    trader_name = Column(String(length=128))
    # 可用现金
    cash = Column(Float)
    # 具体仓位
    positions = relationship("Position", back_populates="sim_account")
    # 市值
    value = Column(Float)
    # 市值+cash
    all_value = Column(Float)

    # 收盘计算
    closing = Column(Boolean)


# 一天可有多条记录
class Position(BusinessBase):
    __tablename__ = 'position'

    id = Column(String(length=128), primary_key=True)
    # 时间
    timestamp = Column(DateTime)
    # 机器人名字
    trader_name = Column(String(length=128))
    # 证券id
    entity_id = Column(String(length=128))
    # 账户id
    sim_account_id = Column(Integer, ForeignKey('sim_account.id'))
    sim_account = relationship("SimAccount", back_populates="positions")

    # 做多数量
    long_amount = Column(Float)
    # 可平多数量
    available_long = Column(Float)
    # 平均做多价格
    average_long_price = Column(Float)

    # 做空数量
    short_amount = Column(Float)
    # 可平空数量
    available_short = Column(Float)
    # 平均做空价格
    average_short_price = Column(Float)

    profit = Column(Float)
    # 市值 或者 占用的保证金(方便起见，总是100%)
    value = Column(Float)
    # 交易类型(0代表T+0,1代表T+1)
    trading_t = Column(Integer)


class Order(BusinessBase):
    __tablename__ = 'order'

    id = Column(String(length=128), primary_key=True)
    # 时间
    timestamp = Column(DateTime)
    # 机器人名字
    trader_name = Column(String(length=128))
    # 证券id
    entity_id = Column(String(length=128))
    # 订单价格
    order_price = Column(Float)
    # 订单数量
    order_amount = Column(Float)
    # 订单类型
    order_type = Column(String(length=64))
    # 订单状态
    status = Column(String(length=64))

    # 产生订单的selector/factor level
    level = Column(String(length=32))


register_schema(providers=['zvt'], db_name='business', schema_base=BusinessBase)
