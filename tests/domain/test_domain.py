# -*- coding: utf-8 -*-
from ..context import init_context

init_context()

from zvdata.domain import global_schemas, get_schemas


def test_all_schemas():
    print(global_schemas)

    print(get_schemas(provider='eastmoney'))
