# -*- coding: utf-8 -*-
from datetime import datetime
from typing import Dict

from pydantic import BaseModel, ConfigDict
from sqlalchemy import Column, String, JSON
from sqlalchemy.orm import declarative_base

from zvt.contract.api import get_db_session
from zvt.contract.register import register_schema
from zvt.contract.schema import Mixin

ZvtInfoBase = declarative_base()


class User(Mixin, ZvtInfoBase):
    __tablename__ = "user"
    added_col = Column(String)
    json_col = Column(JSON)


class UserModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    entity_id: str
    timestamp: datetime
    added_col: str
    json_col: Dict


register_schema(providers=["zvt"], db_name="test", schema_base=ZvtInfoBase)

if __name__ == "__main__":
    user_model = UserModel(
        id="user_cn_jack_2020-01-01",
        entity_id="user_cn_jack",
        timestamp="2020-01-01",
        added_col="test",
        json_col={"a": 1},
    )
    session = get_db_session(provider="zvt", data_schema=User)

    user = session.query(User).filter(User.id == "user_cn_jack_2020-01-01").first()
    print(UserModel.validate(user))
