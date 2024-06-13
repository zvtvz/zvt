# -*- coding: utf-8 -*-
from sqlalchemy import Column, String, Text
from sqlalchemy.orm import declarative_base

from zvt.contract.register import register_schema
from zvt.contract.schema import Mixin

ZvtInfoBase = declarative_base()


class StateMixin(Mixin):
    #: the unique name of the service, e.g. recorder,factor,tag
    state_name = Column(String(length=128))

    #: json string
    state = Column(Text())


class RecorderState(ZvtInfoBase, StateMixin):
    """
    Schema for storing recorder state
    """

    __tablename__ = "recorder_state"


class TaggerState(ZvtInfoBase, StateMixin):
    """
    Schema for storing tagger state
    """

    __tablename__ = "tagger_state"


class FactorState(ZvtInfoBase, StateMixin):
    """
    Schema for storing factor state
    """

    __tablename__ = "factor_state"


register_schema(providers=["zvt"], db_name="zvt_info", schema_base=ZvtInfoBase)


# the __all__ is generated
__all__ = ["StateMixin", "RecorderState", "TaggerState", "FactorState"]
