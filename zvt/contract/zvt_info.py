# -*- coding: utf-8 -*-
from sqlalchemy import Column, String, Text
from sqlalchemy.orm import declarative_base

from zvt.contract.schema import Mixin
from zvt.contract.register import register_schema

ZvtInfoBase = declarative_base()


# 用于保存recorder的状态
class RecorderState(ZvtInfoBase, Mixin):
    __tablename__ = "recoder_state"
    # recorder名字
    recoder_name = Column(String(length=128))

    # json string
    state = Column(Text())


# 用于保存tagger的状态
class TaggerState(ZvtInfoBase, Mixin):
    __tablename__ = "tagger_state"
    # tagger名字
    tagger_name = Column(String(length=128))

    # json string
    state = Column(Text())


register_schema(providers=["zvt"], db_name="zvt_info", schema_base=ZvtInfoBase)
# the __all__ is generated
__all__ = ["ZvtInfoBase", "RecorderState", "TaggerState"]
