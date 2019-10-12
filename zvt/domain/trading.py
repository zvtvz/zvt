# -*- coding: utf-8 -*-
from sqlalchemy import Column, String, Float
from sqlalchemy.ext.declarative import declarative_base

from zvdata.contract import register_schema, register_api
from zvdata import Mixin

TradingBase = declarative_base()


@register_api(provider='eastmoney')
class ManagerTrading(TradingBase, Mixin):
    __tablename__ = 'manager_trading'

    provider = Column(String(length=32))
    code = Column(String(length=32))
    # 日期 变动人 变动数量(股) 交易均价(元) 结存股票(股) 交易方式 董监高管 高管职位 与高管关系
    # 2017-08-11 韦春 200 9.16 -- 竞价交易 刘韬 高管 兄弟姐妹

    # 变动人
    trading_person = Column(String(length=32))
    # 变动数量
    volume = Column(Float)
    # 交易均价
    price = Column(Float)
    # 结存股票
    holding = Column(Float)
    # 交易方式
    trading_way = Column(String(length=32))
    # 董监高管
    manager = Column(String(length=32))
    # 高管职位
    manager_position = Column(String(length=32))
    # 与高管关系
    relationship_with_manager = Column(String(length=32))


@register_api(provider='eastmoney')
class HolderTrading(TradingBase, Mixin):
    __tablename__ = 'holder_trading'

    provider = Column(String(length=32))
    code = Column(String(length=32))

    # 股东名称
    holder_name = Column(String(length=32))
    # 变动数量
    volume = Column(Float)
    # 变动比例
    change_pct = Column(Float)
    # 变动后持股比例
    holding_pct = Column(Float)


@register_api(provider='eastmoney')
class BigDealTrading(TradingBase, Mixin):
    __tablename__ = 'big_deal_trading'

    provider = Column(String(length=32))
    code = Column(String(length=32))

    # 成交额
    turnover = Column(Float)
    # 成交价
    price = Column(Float)
    # 卖出营业部
    sell_broker = Column(String(length=128))
    # 买入营业部
    buy_broker = Column(String(length=128))
    # 折/溢价率
    compare_rate = Column(Float)


@register_api(provider='eastmoney')
class MarginTrading(TradingBase, Mixin):
    __tablename__ = 'margin_trading'

    provider = Column(String(length=32))
    code = Column(String(length=32))

    margin_balance = Column(Float)
    short_balance = Column(Float)


@register_api(provider='eastmoney')
class DragonAndTiger(TradingBase, Mixin):
    __tablename__ = 'dragon_and_tiger'

    provider = Column(String(length=32))
    code = Column(String(length=32))

    # 异动原因
    reason = Column(String(length=128))
    # 成交额
    turnover = Column(Float)
    # 涨幅
    change_pct = Column(Float)
    # 净买入
    net_inflow = Column(Float)

    # 买入营业部
    net_in_dep1 = Column(String(length=128))
    net_in_dep1_money_in = Column(Float)
    net_in_dep1_money_out = Column(Float)
    net_in_dep1_rate = Column(Float)

    net_in_dep2 = Column(String(length=128))
    net_in_dep2_money_in = Column(Float)
    net_in_dep2_money_out = Column(Float)
    net_in_dep2_rate = Column(Float)

    net_in_dep3 = Column(String(length=128))
    net_in_dep3_money_in = Column(Float)
    net_in_dep3_money_out = Column(Float)
    net_in_dep3_rate = Column(Float)

    net_in_dep4 = Column(String(length=128))
    net_in_dep4_money_in = Column(Float)
    net_in_dep4_money_out = Column(Float)
    net_in_dep4_rate = Column(Float)

    net_in_dep5 = Column(String(length=128))
    net_in_dep5_money_in = Column(Float)
    net_in_dep5_money_out = Column(Float)
    net_in_dep5_rate = Column(Float)

    # 卖出营业部
    net_out_dep1 = Column(String(length=128))
    net_out_dep1_money_in = Column(Float)
    net_out_dep1_money_out = Column(Float)
    net_out_dep1_rate = Column(Float)

    net_out_dep2 = Column(String(length=128))
    net_out_dep2_money_in = Column(Float)
    net_out_dep2_money_out = Column(Float)
    net_out_dep2_rate = Column(Float)

    net_out_dep3 = Column(String(length=128))
    net_out_dep3_money_in = Column(Float)
    net_out_dep3_money_out = Column(Float)
    net_out_dep3_rate = Column(Float)

    net_out_dep4 = Column(String(length=128))
    net_out_dep4_money_in = Column(Float)
    net_out_dep4_money_out = Column(Float)
    net_out_dep4_rate = Column(Float)

    net_out_dep5 = Column(String(length=128))
    net_out_dep5_money_in = Column(Float)
    net_out_dep5_money_out = Column(Float)
    net_out_dep5_rate = Column(Float)


register_schema(providers=['eastmoney'], db_name='trading', schema_base=TradingBase)
