# -*- coding: utf-8 -*-
from zvt.factors.algorithm import point_in_range, intersect, intersect_ranges


def test_point_in_range():
    assert point_in_range(1, (1, 2))
    assert point_in_range(2, (1, 2))
    assert point_in_range(1.5, (1, 2))

    assert not point_in_range(0.5, (1, 2))
    assert not point_in_range(2.4, (1, 2))


def test_intersect():
    a = (1, 2)
    b = (1.5, 3)
    assert intersect(a, b) == (1.5, 2)
    assert intersect(b, a) == (1.5, 2)

    a = (1, 2)
    b = (3, 4)
    assert intersect(a, b) == None
    assert intersect(b, a) == None

    a = (1, 4)
    b = (2, 3)
    assert intersect(a, b) == (2, 3)
    assert intersect(b, a) == (2, 3)


def test_intersect_ranges():
    a = (1, 2)
    b = (1.5, 3)
    c = (1.5, 5)
    assert intersect_ranges([a, b, c]) == (1.5, 2)
    assert intersect_ranges([b, a, c]) == (1.5, 2)
    assert intersect_ranges([a, c, b]) == (1.5, 2)

    a = (1, 2)
    b = (1.5, 3)
    c = (4, 5)
    assert intersect_ranges([a, b, c]) == None
    assert intersect_ranges([b, a, c]) == None
    assert intersect_ranges([a, c, b]) == None

    a = (1, 10)
    b = (1.5, 3)
    c = (2, 5)
    assert intersect_ranges([a, b, c]) == (2, 3)
    assert intersect_ranges([b, a, c]) == (2, 3)
    assert intersect_ranges([a, c, b]) == (2, 3)
