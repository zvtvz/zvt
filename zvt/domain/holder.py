# -*- coding: utf-8 -*-
from sqlalchemy import Column, String, DateTime, Enum, Float

from zvt.domain.common import HolderBase, enum_value, ReportPeriod


class TopTenTradableHolder(HolderBase):
    __tablename__ = 'top_ten_tradable_holder'

    id = Column(String(length=128), primary_key=True)
    provider = Column(String(length=32))
    # 报告披露的时间
    timestamp = Column(DateTime)
    security_id = Column(String(length=128))
    code = Column(String(length=32))

    report_period = Column(Enum(ReportPeriod, values_callable=enum_value))
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


class TopTenHolder(HolderBase):
    __tablename__ = 'top_ten_holder'

    id = Column(String(length=128), primary_key=True)
    provider = Column(String(length=32))
    # 报告披露的时间
    timestamp = Column(DateTime)
    security_id = Column(String(length=128))
    code = Column(String(length=32))

    report_period = Column(Enum(ReportPeriod, values_callable=enum_value))
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


class InstitutionalInvestorHolder(HolderBase):
    __tablename__ = 'institutional_investor_holder'

    id = Column(String(length=128), primary_key=True)
    provider = Column(String(length=32))
    # 报告披露的时间
    timestamp = Column(DateTime)
    security_id = Column(String(length=128))
    code = Column(String(length=32))

    report_period = Column(Enum(ReportPeriod, values_callable=enum_value))
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
