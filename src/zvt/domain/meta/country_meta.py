# -*- coding: utf-8 -*-

from sqlalchemy import Column, String, Float
from sqlalchemy.orm import declarative_base

from zvt.contract.register import register_schema, register_entity
from zvt.contract.schema import TradableEntity

CountryMetaBase = declarative_base()


@register_entity(entity_type="country")
class Country(CountryMetaBase, TradableEntity):
    __tablename__ = "country"

    #: 区域
    #: region
    region = Column(String(length=128))
    #: 首都
    #: capital city
    capital_city = Column(String(length=128))
    #: 收入水平
    #: income level
    income_level = Column(String(length=64))
    #: 贷款类型
    #: lending type
    lending_type = Column(String(length=64))
    #: 经度
    #: longitude
    longitude = Column(Float)
    #: 纬度
    #: latitude
    latitude = Column(Float)


register_schema(providers=["wb"], db_name="country_meta", schema_base=CountryMetaBase)


# the __all__ is generated
__all__ = ["Country"]
