# -*- coding: utf-8 -*-
import enum


class StockCategory(enum.Enum):
    # 行业版块
    industry = 'industry'
    # 概念版块
    concept = 'concept'
    # 区域版块
    area = 'area'
    # 上证指数
    sse = 'sse'
    # 深圳指数
    szse = 'szse'
    # 中证指数
    csi = 'csi'
    # 国证指数
    cni = 'cni'
    # ETF
    etf = 'etf'


class ReportPeriod(enum.Enum):
    season1 = 'season1'
    half_year = 'half_year'
    season3 = 'season3'
    year = 'year'


class InstitutionalInvestor(enum.Enum):
    fund = 'fund'
    social_security = 'social_security'
    insurance = 'insurance'
    qfii = 'qfii'
    trust = 'trust'
    broker = 'broker'


# 用于区分不同的财务指标
class CompanyType(enum.Enum):
    qiye = 'qiye'
    baoxian = 'baoxian'
    yinhang = 'yinhang'
    quanshang = 'quanshang'


# make sure import all the domain schemas before using them
from .business import *
from .meta.coin_meta import *
from .dividend_financing import *
from .finance import *
from .holder import *
from .macro import *
from .meta.stock_meta import *
from .money_flow import *
from .trading import *

from .quotes import *
from .factors import *
from .meta import *


def init_schema():
    pass


from zvdata.contract import global_schemas

schemas = []
for item in global_schemas:
    schemas.append(item.__name__)
