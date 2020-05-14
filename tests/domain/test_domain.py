# -*- coding: utf-8 -*-
from ..context import init_test_context

init_test_context()

from zvt.core.contract import zvt_schemas, get_schemas


def test_all_schemas():
    print(zvt_schemas)

    print(get_schemas(provider='eastmoney'))
