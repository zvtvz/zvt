# 数字货币
from sqlalchemy import Column, String, DateTime

from zvt.domain.common import CoinMetaBase


class Coin(CoinMetaBase):
    __tablename__ = 'coin'

    id = Column(String(length=128), primary_key=True)
    timestamp = Column(DateTime)
    exchange = Column(String(length=32))
    type = Column(String(length=64))
    code = Column(String(length=32))
    name = Column(String(length=32))
