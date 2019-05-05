# -*- coding: utf-8 -*-
from sqlalchemy import Column, String, DateTime, Float

from zvt.domain.common import DividendFinancingBase


class DividendFinancing(DividendFinancingBase):
    __tablename__ = 'dividend_financing'

    id = Column(String(length=128), primary_key=True)
    provider = Column(String(length=32))
    timestamp = Column(DateTime)
    security_id = Column(String(length=128))
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


class DividendDetail(DividendFinancingBase):
    __tablename__ = "dividend_detail"

    id = Column(String(length=128), primary_key=True)
    provider = Column(String(length=32))
    # =公告日
    timestamp = Column(DateTime)
    security_id = Column(String(length=128))
    code = Column(String(length=32))

    # 公告日
    announce_date = Column(DateTime)
    # 股权登记日
    record_date = Column(DateTime)
    # 除权除息日
    dividend_date = Column(DateTime)

    # 方案
    dividend = Column(String(length=128))


class SPODetail(DividendFinancingBase):
    __tablename__ = "spo_detail"

    id = Column(String(length=128), primary_key=True)
    provider = Column(String(length=32))
    timestamp = Column(DateTime)
    security_id = Column(String(length=128))
    code = Column(String(length=32))

    spo_issues = Column(Float)
    spo_price = Column(Float)
    spo_raising_fund = Column(Float)


class RightsIssueDetail(DividendFinancingBase):
    __tablename__ = "rights_issue_detail"

    id = Column(String(length=128), primary_key=True)
    provider = Column(String(length=32))
    timestamp = Column(DateTime)
    security_id = Column(String(length=128))
    code = Column(String(length=32))

    # 配股
    rights_issues = Column(Float)
    rights_issue_price = Column(Float)
    rights_raising_fund = Column(Float)
