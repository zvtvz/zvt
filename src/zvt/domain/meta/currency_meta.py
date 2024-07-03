# -*- coding: utf-8 -*-

from sqlalchemy.orm import declarative_base

from zvt.contract.register import register_schema, register_entity
from zvt.contract.schema import TradableEntity

CurrencyMetaBase = declarative_base()


@register_entity(entity_type="currency")
class Currency(CurrencyMetaBase, TradableEntity):
    __tablename__ = "currency"


register_schema(providers=["em"], db_name="currency_meta", schema_base=CurrencyMetaBase)


# the __all__ is generated
__all__ = ["Currency"]
