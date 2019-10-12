# -*- coding: utf-8 -*-
from ..context import init_test_context

init_test_context()

from zvdata.contract import global_schemas, get_schemas


def test_all_schemas():
    print(global_schemas)

    print(get_schemas(provider='eastmoney'))
