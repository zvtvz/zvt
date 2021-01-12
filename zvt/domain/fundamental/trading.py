# -*- coding: utf-8 -*-
from sqlalchemy import Column, String, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base

from zvt.contract import Mixin
from zvt.contract.register import register_schema

TradingBase = declarative_base()


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



class LockedShares(TradingBase, Mixin):
    """
    限售解禁
    """
    __tablename__ = 'locked_shares'
    """
    day: 解禁日期
    code: 股票代码
    num: 解禁股数
    rate1: 解禁股数/总股本
    rate2: 解禁股数/总流通股本
    """
    provider = Column(String(length=32))
    code = Column(String(length=32))
    end_date = Column(DateTime)

    # 解禁股数
    locked_num = Column(Float)
    # 解禁股数/总股本
    locked_rate1 = Column(Float)
    # 解禁股数/总流通股本
    locked_rate2 = Column(Float)



class EquityPledge(TradingBase, Mixin):
    """
    股权质押
    """
    __tablename__ = 'equity_pledge'

    provider = Column(String(length=32))
    code = Column(String(length=32))
    pub_date = Column(DateTime)

    # 出质人 将资产质押出去的人成为出质人
    pledgor = Column(String(length=100))
    # 质权人
    pledgee = Column(String(length=100))
    # 质押事项
    pledge_item = Column(String(length=500))
    # 质押股份性质	varchar(120)
    pledge_nature = Column(String(length=120))
    # 质押数量
    pledge_number =  Column(Float)
    # 占总股本比例 %
    pledge_total_ratio =  Column(Float)
    # 质押起始日
    start_date =  Column(DateTime)
    # 质押终止日
    end_date = Column(DateTime)
    # 质押解除日
    unpledged_date = Column(DateTime)
    # 是否质押式回购交易	char(1)
    is_buy_back = Column(String(length=1))


class HolderTrading(TradingBase, Mixin):
    __tablename__ = 'holder_trading'

    def get_data_map(self):
        return {
            'NOTICEDATE': 'report_date',  # 公告日期
            'SHAREHDNAME': 'holder_name',  # 股东名称
            'SHAREHDTYPE': 'holder_share_type',  # 股东类型
            'IS_controller': 'holder_controller',  # 是否实际控制人
            'POSITION1': 'holder_positions',  # 高管职务
            'FX': 'holder_direction',  # 方向
            'BDHCGZS': 'holder_share_af',  # 变动后_持股总数(万股)
            'CHANGENUM': 'volume',  # 变动_流通股数量(万股) 变动股份数量
            'BDHCGBL': 'holding_pct',  # 变动后_占总股本比例(%)
            'JYPJJ': 'price',  # 交易均价(元)
            'BDQSRQ': 'holder_start_date',  # 变动起始日期
            'BDJZRQ': 'holder_end_date',  # 变动截止日期
            'CLB_REMARK': 'holder_remark',  # 说明
        }
    provider = Column(String(length=32))
    code = Column(String(length=32))

    # 股东名称
    holder_name = Column(String(length=150))
    # 变动数量
    volume = Column(Float)
    # 变动比例
    change_pct = Column(Float)
    # 变动后持股比例
    holding_pct = Column(Float)

    # 股东类型
    holder_share_type = Column(String(length=32))
    # 是否实际控制人
    holder_controller = Column(String(length=32))
    # 高管职务
    holder_positions = Column(String(length=32))
    # 方向
    holder_direction = Column(String(length=32))
    # 变动后_持股总数
    holder_share_af = Column(Float)
    # 交易均价
    price = Column(String(length=32))
    # 变动起始日期
    holder_start_date = Column(DateTime)
    # 变动截止日期
    holder_end_date = Column(DateTime)
    # 变动原因 说明
    holder_remark = Column(String(length=2000))
    # 变动前_持股总数(万股)
    holder_share_bf = Column(Float)


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


class MarginTrading(TradingBase, Mixin):
    __tablename__ = 'margin_trading'

    provider = Column(String(length=32))
    code = Column(String(length=32))

    margin_balance = Column(Float)
    short_balance = Column(Float)


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


register_schema(providers=['eastmoney', 'joinquant','emquantapi'], db_name='trading', schema_base=TradingBase)

__all__ = ['LockedShares','EquityPledge','ManagerTrading', 'HolderTrading', 'MarginTrading', 'BigDealTrading', 'DragonAndTiger']
