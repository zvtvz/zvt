# -*- coding: utf-8 -*-

from sqlalchemy.orm import declarative_base

from zvt.contract import TradableEntity
from zvt.contract.register import register_schema, register_entity

CBondBase = declarative_base()


#: 美股
@register_entity(entity_type="cbond")
class CBond(CBondBase, TradableEntity):
    __tablename__ = "cbond"


register_schema(providers=["em"], db_name="cbond_meta", schema_base=CBondBase)


# the __all__ is generated
__all__ = ["CBond"]
