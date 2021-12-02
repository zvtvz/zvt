# -*- coding: utf-8 -*-
import logging

import eastmoneypy

logger = logging.getLogger(__name__)


def add_to_eastmoney(codes, group, entity_type="stock", over_write=True):
    if over_write:
        try:
            eastmoneypy.del_group(group_name=group)
        except:
            pass
    try:
        eastmoneypy.create_group(group_name=group)
    except:
        pass

    for code in codes:
        eastmoneypy.add_to_group(code=code, entity_type=entity_type, group_name=group)
