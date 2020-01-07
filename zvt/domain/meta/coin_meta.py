# 数字货币
from sqlalchemy.ext.declarative import declarative_base

from zvdata import EntityMixin
from zvdata.contract import register_schema, register_entity

CoinMetaBase = declarative_base()


@register_entity(entity_type='coin')
class Coin(CoinMetaBase, EntityMixin):
    __tablename__ = 'coin'


register_schema(providers=['ccxt'], db_name='coin_meta', schema_base=CoinMetaBase)

__all__ = ['Coin']
