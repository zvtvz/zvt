# -*- coding: utf-8 -*-
import inspect

import zvt.trader.examples
from zvt.core import Constructor
from zvt.trader.trader import Trader


def get_trader_classes():
    cls_members = inspect.getmembers(zvt.trader.examples, inspect.isclass)

    return [(name, cls) for name, cls in cls_members if issubclass(cls, Trader) and cls != Trader]


def get_class_constructor_meta(cls):
    if issubclass(cls, Constructor):
        return cls.get_constructor_meta()

    raise Exception('{} is not Constructor'.format(cls))


if __name__ == '__main__':
    for name, cls in get_trader_classes():
        print(get_class_constructor_meta(cls))
