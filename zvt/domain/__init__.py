# -*- coding: utf-8 -*-
import enum


class BlockCategory(enum.Enum):
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
    # 有些基金的2，4季报只有10大持仓，半年报和年报有详细持仓，需要区别对待
    season1 = 'season1'
    season2 = 'season2'
    season3 = 'season3'
    season4 = 'season4'
    half_year = 'half_year'
    year = 'year'


class InstitutionalInvestor(enum.Enum):
    # 基金
    fund = 'fund'
    # 社保
    social_security = 'social_security'
    # 保险
    insurance = 'insurance'
    # 外资
    qfii = 'qfii'
    # 信托
    trust = 'trust'
    # 券商
    broker = 'broker'
    # 公司
    other = 'other'


# 用于区分不同的财务指标
class CompanyType(enum.Enum):
    qiye = 'qiye'
    baoxian = 'baoxian'
    yinhang = 'yinhang'
    quanshang = 'quanshang'

# the __all__ is generated
__all__ = ['BlockCategory', 'ReportPeriod', 'InstitutionalInvestor', 'CompanyType']

# __init__.py structure:
# common code of the package
# export interface in __all__ which contains __all__ of its sub modules

# import all from submodule misc
from .misc import *
from .misc import __all__ as _misc_all
__all__ += _misc_all

# import all from submodule quotes
from .quotes import *
from .quotes import __all__ as _quotes_all
__all__ += _quotes_all

# import all from submodule meta
from .meta import *
from .meta import __all__ as _meta_all
__all__ += _meta_all

# import all from submodule fundamental
from .fundamental import *
from .fundamental import __all__ as _fundamental_all
__all__ += _fundamental_all

# import all from submodule trader_info
from .trader_info import *
from .trader_info import __all__ as _trader_info_all
__all__ += _trader_info_all