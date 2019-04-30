# -*- coding: utf-8 -*-
from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, Float, Integer
from sqlalchemy.orm import relationship

# business data
from zvt.domain.common import BusinessBase


class SimAccount(BusinessBase):
    __tablename__ = 'sim_accounts'

    id = Column(String(length=128), primary_key=True)
    # 机器人名字
    trader_name = Column(String(length=128))
    # 所用的模型
    model_name = Column(String(length=128))
    # 可用现金
    cash = Column(Float)
    # 具体仓位
    positions = relationship("Position", back_populates="sim_account")
    # 市值
    value = Column(Float)
    # 市值+cash
    all_value = Column(Float)
    # 时间
    timestamp = Column(DateTime)

    # 收盘计算
    closing = Column(Boolean)


class Position(BusinessBase):
    __tablename__ = 'positions'

    id = Column(String(length=128), primary_key=True)
    # 证券id
    security_id = Column(String(length=128))
    # 账户id
    sim_account_id = Column(Integer, ForeignKey('sim_accounts.id'))
    sim_account = relationship("SimAccount", back_populates="positions")
    # 时间
    timestamp = Column(DateTime)

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
