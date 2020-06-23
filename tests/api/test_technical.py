# -*- coding: utf-8 -*-
from zvt.contract.api import get_entities
from ..context import init_test_context

init_test_context()



def test_basic_get_securities():
    items = get_entities(entity_type='stock', provider='eastmoney')
    print(items)
    items = get_entities(entity_type='index', provider='eastmoney')
    print(items)