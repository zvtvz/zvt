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


register_schema(providers=['eastmoney'], db_name='holder', schema_base=HolderBase)

__all__ = ['TopTenTradableHolder', 'TopTenHolder', 'InstitutionalInvestorHolder']
