# -*- coding: utf-8 -*-
from sqlalchemy import Column, String, Float, BIGINT
from sqlalchemy.orm import declarative_base

from zvt.contract import Mixin
from zvt.contract.register import register_schema

MacroBase = declarative_base()


class Economy(MacroBase, Mixin):
    # https://datatopics.worldbank.org/world-development-indicators//themes/economy.html
    __tablename__ = "economy"

    code = Column(String(length=32))
    name = Column(String(length=32))
    population = Column(BIGINT)

    gdp = Column(Float)
    gdp_per_capita = Column(Float)
    gdp_per_employed = Column(Float)
    gdp_growth = Column(Float)
    agriculture_growth = Column(Float)
    industry_growth = Column(Float)
    manufacturing_growth = Column(Float)
    service_growth = Column(Float)
    consumption_growth = Column(Float)
    capital_growth = Column(Float)
    exports_growth = Column(Float)
    imports_growth = Column(Float)

    gni = Column(Float)
    gni_per_capita = Column(Float)

    gross_saving = Column(Float)
    cpi = Column(Float)
    unemployment_rate = Column(Float)
    fdi_of_gdp = Column(Float)


register_schema(providers=["wb"], db_name="macro", schema_base=MacroBase)


# the __all__ is generated
__all__ = ["Economy"]
