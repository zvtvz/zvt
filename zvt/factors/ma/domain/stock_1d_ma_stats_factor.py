# -*- coding: utf-8 -*-
from sqlalchemy.ext.declarative import declarative_base

from zvt.contract.register import register_schema
from zvt.factors.ma.domain.common import MaStatsFactorCommon

Stock1dMaStatsFactorBase = declarative_base()


class Stock1dMaStatsFactor(Stock1dMaStatsFactorBase, MaStatsFactorCommon):
    __tablename__ = 'stock_1d_ma_stats_factor'


register_schema(providers=['zvt'], db_name='stock_1d_ma_stats_factor', schema_base=Stock1dMaStatsFactorBase)
# the __all__ is generated
__all__ = ['Stock1dMaStatsFactor']