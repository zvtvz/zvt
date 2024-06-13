# -*- coding: utf-8 -*-
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class CustomModel(BaseModel):
    model_config = ConfigDict(from_attributes=True, allow_inf_nan=True)


class MixinModel(CustomModel):
    id: str
    entity_id: str
    timestamp: datetime


# the __all__ is generated
__all__ = ["CustomModel", "MixinModel"]
