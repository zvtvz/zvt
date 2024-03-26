# -*- coding: utf-8 -*-
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class MixinModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    entity_id: str
    timestamp: datetime
