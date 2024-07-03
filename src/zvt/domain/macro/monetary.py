# -*- coding: utf-8 -*-
from sqlalchemy import Column, String, Float
from sqlalchemy.orm import declarative_base

from zvt.contract import Mixin
from zvt.contract.register import register_schema

MonetaryBase = declarative_base()


class TreasuryYield(MonetaryBase, Mixin):
    __tablename__ = "treasury_yield"

    code = Column(String(length=32))

    # 2年期
    yield_2 = Column(Float)
    # 5年期
    yield_5 = Column(Float)
    # 10年期
    yield_10 = Column(Float)
    # 30年期
    yield_30 = Column(Float)


register_schema(providers=["em"], db_name="monetary", schema_base=MonetaryBase)


# the __all__ is generated
__all__ = ["TreasuryYield"]
