# -*- coding: utf-8 -*-
from sqlalchemy import Column, String, Float
from sqlalchemy.orm import declarative_base

from zvt.contract import Mixin
from zvt.contract.register import register_schema

TradingBase = declarative_base()


class ManagerTrading(TradingBase, Mixin):
    __tablename__ = "manager_trading"

    provider = Column(String(length=32))
    code = Column(String(length=32))
    #: 日期 变动人 变动数量(股) 交易均价(元) 结存股票(股) 交易方式 董监高管 高管职位 与高管关系
    #: 2017-08-11 韦春 200 9.16 -- 竞价交易 刘韬 高管 兄弟姐妹

    #: 变动人
    trading_person = Column(String(length=32))
    #: 变动数量
    volume = Column(Float)
    #: 交易均价
    price = Column(Float)
    #: 结存股票
    holding = Column(Float)
    #: 交易方式
    trading_way = Column(String(length=32))
    #: 董监高管
    manager = Column(String(length=32))
    #: 高管职位
    manager_position = Column(String(length=32))
    #: 与高管关系
    relationship_with_manager = Column(String(length=32))


class HolderTrading(TradingBase, Mixin):
    __tablename__ = "holder_trading"

    provider = Column(String(length=32))
    code = Column(String(length=32))

    #: 股东名称
    holder_name = Column(String(length=32))
    #: 变动数量
    volume = Column(Float)
    #: 变动比例
    change_pct = Column(Float)
    #: 变动后持股比例
    holding_pct = Column(Float)


class BigDealTrading(TradingBase, Mixin):
    __tablename__ = "big_deal_trading"

    provider = Column(String(length=32))
    code = Column(String(length=32))

    #: 成交额
    turnover = Column(Float)
    #: 成交价
    price = Column(Float)
    #: 卖出营业部
    sell_broker = Column(String(length=128))
    #: 买入营业部
    buy_broker = Column(String(length=128))
    #: 折/溢价率
    compare_rate = Column(Float)


class MarginTrading(TradingBase, Mixin):
    __tablename__ = "margin_trading"
    code = Column(String(length=32))

    #: 融资余额(元）
    fin_value = Column(Float)
    #: 融资买入额（元）
    fin_buy_value = Column(Float)
    #: 融资偿还额（元）
    fin_refund_value = Column(Float)
    #: 融券余量（股）
    sec_value = Column(Float)
    #: 融券卖出量（股）
    sec_sell_value = Column(Float)
    #: 融券偿还量（股）
    sec_refund_value = Column(Float)
    #: 融资融券余额（元）
    fin_sec_value = Column(Float)


class DragonAndTiger(TradingBase, Mixin):
    __tablename__ = "dragon_and_tiger"

    code = Column(String(length=32))
    name = Column(String(length=32))

    #: 异动原因
    reason = Column(String(length=128))
    #: 成交额
    turnover = Column(Float)
    #: 涨幅
    change_pct = Column(Float)
    #: 净买入
    net_in = Column(Float)

    #: 买入营业部
    dep1 = Column(String(length=128))
    dep1_in = Column(Float)
    dep1_out = Column(Float)
    dep1_rate = Column(Float)

    dep2 = Column(String(length=128))
    dep2_in = Column(Float)
    dep2_out = Column(Float)
    dep2_rate = Column(Float)

    dep3 = Column(String(length=128))
    dep3_in = Column(Float)
    dep3_out = Column(Float)
    dep3_rate = Column(Float)

    dep4 = Column(String(length=128))
    dep4_in = Column(Float)
    dep4_out = Column(Float)
    dep4_rate = Column(Float)

    dep5 = Column(String(length=128))
    dep5_in = Column(Float)
    dep5_out = Column(Float)
    dep5_rate = Column(Float)

    #: 卖出营业部
    dep_1 = Column(String(length=128))
    dep_1_in = Column(Float)
    dep_1_out = Column(Float)
    dep_1_rate = Column(Float)

    dep_2 = Column(String(length=128))
    dep_2_in = Column(Float)
    dep_2_out = Column(Float)
    dep_2_rate = Column(Float)

    dep_3 = Column(String(length=128))
    dep_3_in = Column(Float)
    dep_3_out = Column(Float)
    dep_3_rate = Column(Float)

    dep_4 = Column(String(length=128))
    dep_4_in = Column(Float)
    dep_4_out = Column(Float)
    dep_4_rate = Column(Float)

    dep_5 = Column(String(length=128))
    dep_5_in = Column(Float)
    dep_5_out = Column(Float)
    dep_5_rate = Column(Float)


register_schema(
    providers=["em", "eastmoney", "joinquant"], db_name="trading", schema_base=TradingBase, entity_type="stock"
)


# the __all__ is generated
__all__ = ["ManagerTrading", "HolderTrading", "BigDealTrading", "MarginTrading", "DragonAndTiger"]
