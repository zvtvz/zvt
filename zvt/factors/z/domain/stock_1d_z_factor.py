# -*- coding: utf-8 -*-
from sqlalchemy.ext.declarative import declarative_base

from zvt.contract.register import register_schema
from zvt.factors.z.domain.common import ZFactorCommon

Stock1dZFactorBase = declarative_base()


class Stock1dZFactor(Stock1dZFactorBase, ZFactorCommon):
    __tablename__ = "stock_1d_z_factor"


register_schema(providers=["zvt"], db_name="stock_1d_z_factor", schema_base=Stock1dZFactorBase, entity_type="stock")
# the __all__ is generated
__all__ = ["Stock1dZFactor"]
