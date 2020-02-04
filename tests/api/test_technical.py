# -*- coding: utf-8 -*-
from ..context import init_test_context

init_test_context()

from zvt.api.quote import get_entities


def test_basic_get_securities():
    items = get_entities(entity_type='stock', provider='eastmoney')
    print(items)
    items = get_entities(entity_type='index', provider='eastmoney')
    print(items)
    items = get_entities(entity_type='coin', provider='ccxt')
    print(items)
