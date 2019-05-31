# -*- coding: utf-8 -*-
from sqlalchemy import Column, String, DateTime, Float

from zvt.domain.common import MoneyFlowBase


# 板块资金流向
class IndexMoneyFlow(MoneyFlowBase):
    __tablename__ = 'index_money_flow'

    id = Column(String(length=128), primary_key=True)
    timestamp = Column(DateTime)
    security_id = Column(String(length=128))
    code = Column(String(length=32))
    name = Column(String(length=32))

    # 收盘价
    close = Column(Float)
    change_pct = Column(Float)
    turnover_rate = Column(Float)

    # 净流入
    net_inflows = Column(Float)
    # 净流入率
    net_inflow_rate = Column(Float)

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


class StockMoneyFlow(MoneyFlowBase):
    __tablename__ = 'stock_money_flow'

    id = Column(String(length=128), primary_key=True)
    timestamp = Column(DateTime)
    security_id = Column(String(length=128))
    code = Column(String(length=32))
    name = Column(String(length=32))

    # 收盘价
    close = Column(Float)
    change_pct = Column(Float)
    turnover_rate = Column(Float)

    # 净流入
    net_inflows = Column(Float)
    # 净流入率
    net_inflow_rate = Column(Float)

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
