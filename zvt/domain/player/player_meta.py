# -*- coding: utf-8 -*-

from sqlalchemy.ext.declarative import declarative_base

from zvt.contract.register import register_schema
from zvt.contract.schema import Player

PlayerMetaBase = declarative_base()


# 个股
class PlayerMeta(PlayerMetaBase, Player):
    __tablename__ = 'player_meta'


register_schema(providers=['eastmoney'], db_name='player_meta', schema_base=PlayerMetaBase)
# the __all__ is generated
__all__ = ['PlayerMeta']