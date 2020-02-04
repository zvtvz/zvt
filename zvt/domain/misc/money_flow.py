# -*- coding: utf-8 -*-
from sqlalchemy import Column, String, Float
from sqlalchemy.ext.declarative import declarative_base

from zvdata import Mixin
from zvdata.contract import register_schema, register_api

MoneyFlowBase = declarative_base()


# 板块资金流向
@register_api(provider='sina')
class BlockMoneyFlow(MoneyFlowBase, Mixin):
    __tablename__ = 'block_money_flow'

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


@register_api(provider='sina')
class StockMoneyFlow(MoneyFlowBase, Mixin):
    __tablename__ = 'stock_money_flow'

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


register_schema(providers=['sina'], db_name='money_flow', schema_base=MoneyFlowBase)

__all__ = ['BlockMoneyFlow', 'StockMoneyFlow']
