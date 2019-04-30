# -*- coding: utf-8 -*-
from sqlalchemy import Column, String, DateTime, Enum, Float

from zvt.domain.common import Provider, enum_value, MoneyFlowBase


class MoneyFlow(MoneyFlowBase):
    __tablename__ = 'money_flow'

    id = Column(String(length=128), primary_key=True)
    provider = Column(Enum(Provider, values_callable=enum_value), primary_key=True)
    timestamp = Column(DateTime)
    security_id = Column(String(length=128))
    code = Column(String(length=32))

    # 主力=超大单+大单
    net_main_inflows = Column(Float)
    net_main_inflow_rate = Column(Float)
    # 超大单
    net_huge_inflows = Column(Float)
    net_huge_inflow_rate = Column(Float)
    # 大单
    net_big_inflows = Column(Float)
    net_big_inflow_rate = Column(Float)

    # 中单
    net_medium_inflows = Column(Float)
    net_medium_inflow_rate = Column(Float)
    # 小单
    net_small_inflows = Column(Float)
    net_small_inflow_rate = Column(Float)
