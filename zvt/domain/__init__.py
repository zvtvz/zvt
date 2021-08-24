# -*- coding: utf-8 -*-
import enum


class BlockCategory(enum.Enum):
    # 行业版块
    industry = 'industry'
    # 概念版块
    concept = 'concept'
    # 区域版块
    area = 'area'


class IndexCategory(enum.Enum):
    # 中国指数提供商：
    # 中证指数公司 http://www.csindex.com.cn/zh-CN
    # 上证指数(上交所标的) 中证指数(沪深)

    # 国证指数公司 http://www.cnindex.com.cn/index.html
    # 深证指数(深交所标的) 国证指数(沪深)

    # 规模指数
    # 常见的上证指数，深证指数等
    scope = 'scope'
    # 行业指数
    industry = 'industry'
    # 风格指数
    style = 'style'
    # 主题指数
    #
    # 策略指数
    #
    # 综合指数
    #
    # 债券指数
    #
    # 基金指数
    fund = 'fund'
    # 定制指数
    #
    # 人民币指数
    #
    # 跨境指数
    #
    # 其他指数


class ReportPeriod(enum.Enum):
    # 有些基金的2，4季报只有10大持仓，半年报和年报有详细持仓，需要区别对待
    season1 = 'season1'
    season2 = 'season2'
    season3 = 'season3'
    season4 = 'season4'
    half_year = 'half_year'
    year = 'year'


# 用于区分不同的财务指标
class CompanyType(enum.Enum):
    qiye = 'qiye'
    baoxian = 'baoxian'
    yinhang = 'yinhang'
    quanshang = 'quanshang'


# the __all__ is generated
__all__ = ['BlockCategory', 'IndexCategory', 'ReportPeriod', 'CompanyType']

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

# import all from submodule macro
from .macro import *
from .macro import __all__ as _macro_all
__all__ += _macro_all

# import all from submodule trader_info
from .trader_info import *
from .trader_info import __all__ as _trader_info_all
__all__ += _trader_info_all

# import all from submodule actor
from .actor import *
from .actor import __all__ as _actor_all
__all__ += _actor_all