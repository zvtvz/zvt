# -*- coding: utf-8 -*-
from sqlalchemy import Column, String, DateTime, Float
from sqlalchemy.ext.declarative import declarative_base

from zvt.contract import Mixin
from zvt.contract.register import register_schema

HolderBase = declarative_base()


class TopTenTradableHolder(HolderBase, Mixin):
    __tablename__ = 'top_ten_tradable_holder'

    provider = Column(String(length=32))
    code = Column(String(length=32))

    report_period = Column(String(length=32))
    report_date = Column(DateTime)

    # 股东代码
    holder_code = Column(String(length=32))
    # 股东名称
    holder_name = Column(String(length=32))
    # 持股数
    shareholding_numbers = Column(Float)
    # 持股比例
    shareholding_ratio = Column(Float)
    # 变动
    change = Column(Float)
    # 变动比例
    change_ratio = Column(Float)


holdtradedetail_map = {
    'NOTICEDATE': 'report_date',  # 公告日期
    'SHAREHDNAME': 'holder_name',  # 股东名称
    'SHAREHDTYPE': 'holder_share_type',  # 股东类型
    'IS_controller': 'holder_controller',  # 是否实际控制人
    'POSITION1': 'holder_positions',  # 高管职务
    'FX': 'holder_direction',  # 方向
    'BDHCGZS': 'holder_share_af',  # 变动后_持股总数(万股)
    'CHANGENUM': 'holder_share_ch',  # 变动_流通股数量(万股) 变动股份数量
    'BDHCGBL': 'BDHCGBL',  # 变动后_占总股本比例(%)
    'JYPJJ': 'holder_avg_price',  # 成交均价(元)
    'BDQSRQ': 'holder_start_date',  # 变动起始日期
    'BDJZRQ': 'holder_end_date',  # 变动截止日期
    'CLB_REMARK': 'holder_remark',  # 说明
}


class HoldTradeDetail(HolderBase, Mixin):
    """
    高管及相关人员持股变动
    """
    __tablename__ = 'holder_trade_detail'

    def get_data_map(self):
        return holdtradedetail_map

    provider = Column(String(length=32))
    code = Column(String(length=32))
    # 公告日期
    report_date = Column(DateTime)

    # 股东名称
    holder_name = Column(String(length=32))
    # 股东类型
    holder_share_type = Column(String(length=32))
    # 是否实际控制人
    holder_controller = Column(String(length=32))
    # 高管职务
    holder_positions = Column(String(length=32))
    # 方向
    holder_direction = Column(String(length=32))
    # 变动后_持股总数(万股)
    holder_share_af = Column(Float)
    # 变动股份数量(万股)
    holder_share_ch = Column(Float)
    # 变动比例（千分位）
    holder_change_prop   = Column(Float)
    # 成交均价
    holder_avg_price = Column(Float)
    # 变动起始日期
    holder_start_date= Column(DateTime)
    # 变动截止日期
    holder_end_date= Column(DateTime)
    # 变动原因 说明
    holder_remark = Column(String(length=300))

    # 变动前_持股总数(万股)
    holder_share_bf = Column(Float)


class TopTenHolder(HolderBase, Mixin):

    __tablename__ = 'top_ten_holder'

    provider = Column(String(length=32))
    code = Column(String(length=32))

    report_period = Column(String(length=32))
    report_date = Column(DateTime)

    # 股东代码
    holder_code = Column(String(length=32))
    # 股东名称
    holder_name = Column(String(length=32))
    # 持股数
    shareholding_numbers = Column(Float)
    # 持股比例
    shareholding_ratio = Column(Float)
    # 变动
    change = Column(Float)
    # 变动比例
    change_ratio = Column(Float)


class InstitutionalInvestorHolder(HolderBase, Mixin):
    __tablename__ = 'institutional_investor_holder'

    provider = Column(String(length=32))
    code = Column(String(length=32))

    report_period = Column(String(length=32))
    report_date = Column(DateTime)

    # 机构类型
    institutional_investor_type = Column(String(length=64))
    # 股东代码
    holder_code = Column(String(length=32))
    # 股东名称
    holder_name = Column(String(length=32))
    # 持股数
    shareholding_numbers = Column(Float)
    # 持股比例
    shareholding_ratio = Column(Float)


register_schema(providers=['eastmoney', 'emquantapi'], db_name='holder', schema_base=HolderBase)

__all__ = ['TopTenTradableHolder', 'TopTenHolder', 'InstitutionalInvestorHolder', 'HoldTradeDetail']
