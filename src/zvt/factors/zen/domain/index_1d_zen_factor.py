# -*- coding: utf-8 -*-
from sqlalchemy.ext.declarative import declarative_base

from zvt.contract.register import register_schema
from zvt.factors.zen.domain.common import ZenFactorCommon

Index1dZenFactorBase = declarative_base()


class Index1dZenFactor(Index1dZenFactorBase, ZenFactorCommon):
    __tablename__ = "index_1d_zen_factor"


register_schema(providers=["zvt"], db_name="index_1d_zen_factor", schema_base=Index1dZenFactorBase, entity_type="index")


# the __all__ is generated
__all__ = ["Index1dZenFactor"]
