# -*- coding: utf-8 -*-
from sqlalchemy.ext.declarative import declarative_base

from zvt.contract.register import register_schema
from zvt.factors.zen.domain.common import ZenFactorCommon

Stock1dZenFactorBase = declarative_base()


class Stock1dZenFactor(Stock1dZenFactorBase, ZenFactorCommon):
    __tablename__ = 'stock_1d_zen_factor'


register_schema(providers=['zvt'], db_name='stock_1d_zen_factor', schema_base=Stock1dZenFactorBase)
# the __all__ is generated
__all__ = ['Stock1dZenFactor']
