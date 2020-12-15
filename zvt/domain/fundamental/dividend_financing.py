# -*- coding: utf-8 -*-
from sqlalchemy import Column, String, DateTime, Float
from sqlalchemy.ext.declarative import declarative_base

from zvt.contract import Mixin
from zvt.contract.register import register_schema

DividendFinancingBase = declarative_base()


class DividendFinancing(DividendFinancingBase, Mixin):
    __tablename__ = 'dividend_financing'

    provider = Column(String(length=32))
    code = Column(String(length=32))

    # 分红总额
    dividend_money = Column(Float)

    # 新股
    ipo_issues = Column(Float)
    ipo_raising_fund = Column(Float)

    # 增发
    spo_issues = Column(Float)
    spo_raising_fund = Column(Float)
    # 配股
    rights_issues = Column(Float)
    rights_raising_fund = Column(Float)


class DividendDetail(DividendFinancingBase, Mixin):
    __tablename__ = "dividend_detail"

    provider = Column(String(length=32))
    code = Column(String(length=32))

    # 公告日
    announce_date = Column(DateTime)
    # 股权登记日
    record_date = Column(DateTime)
    # 除权除息日
    dividend_date = Column(DateTime)

    # 方案
    dividend = Column(String(length=128))


class SpoDetail(DividendFinancingBase, Mixin):
    __tablename__ = "spo_detail"

    provider = Column(String(length=32))
    code = Column(String(length=32))

    spo_issues = Column(Float)
    spo_price = Column(Float)
    spo_raising_fund = Column(Float)


class RightsIssueDetail(DividendFinancingBase, Mixin):
    __tablename__ = "rights_issue_detail"

    provider = Column(String(length=32))
    code = Column(String(length=32))

    # 配股
    rights_issues = Column(Float)
    rights_issue_price = Column(Float)
    rights_raising_fund = Column(Float)


register_schema(providers=['eastmoney'], db_name='dividend_financing', schema_base=DividendFinancingBase, entity_type='stock')

# the __all__ is generated
__all__ = ['DividendFinancing', 'DividendDetail', 'SpoDetail', 'RightsIssueDetail']