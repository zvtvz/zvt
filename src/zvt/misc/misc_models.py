# -*- coding: utf-8 -*-
from datetime import datetime

from zvt.contract.model import CustomModel


class TimeMessage(CustomModel):
    # 时间
    timestamp: datetime
    # 信息
    message: str


# the __all__ is generated
__all__ = ["TimeMessage"]
