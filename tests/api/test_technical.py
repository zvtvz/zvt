# -*- coding: utf-8 -*-
from ..context import init_test_context

init_test_context()

from zvt.api.quote import get_entities, get_securities_in_blocks


def test_basic_get_securities():
    items = get_entities(entity_type='stock', provider='eastmoney')
    print(items)
    items = get_entities(entity_type='index', provider='eastmoney')
    print(items)
    items = get_entities(entity_type='coin', provider='ccxt')
    print(items)


def test_get_security_blocks():
    hs300 = get_securities_in_blocks(names=['HS300_'])
    assert len(hs300) == 300
    assert 'stock_sz_000338' in hs300
