# -*- coding: utf-8 -*-
from zvt.contract.api import get_entities
from zvt.utils.utils import iterate_with_step, to_str, float_to_pct


def test_iterate_with_step():
    data = range(1000)
    first = None
    last = None
    for sub_data in iterate_with_step(data):
        if not first:
            first = sub_data
        last = sub_data

    assert first[0] == 0
    assert first[-1] == 99

    assert last[0] == 900
    assert last[-1] == 999


def test_iterate_entities():
    data = get_entities(entity_type="stock")
    first = None
    last = None
    for sub_data in iterate_with_step(data):
        if first is None:
            first = sub_data
        last = sub_data

    assert len(first) == 100
    assert len(last) <= 100


def test_to_str():
    assert to_str(None) is None
    assert to_str("") is None
    assert to_str("a") == "a"
    assert to_str(["a", "b"]) == "a;b"
    assert to_str([1, 2]) == "1;2"


def test_float_to_pct():
    assert float_to_pct(0.1) == "10.00%"
    assert float_to_pct(0.111) == "11.10%"
    assert float_to_pct(0.8) == "80.00%"
    assert float_to_pct(0.555) == "55.50%"
    assert float_to_pct(0.33333) == "33.33%"
