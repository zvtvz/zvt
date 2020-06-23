# -*- coding: utf-8 -*-
import json

from sqlalchemy.sql.elements import BinaryExpression

from zvt.contract.api import table_name_to_domain_name


class CustomJsonEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, BinaryExpression):
            sql_str = str(obj)
            left, expression, _ = sql_str.split()
            table_name, col = left.split('.')
            value = obj.right.value
            domain_name = table_name_to_domain_name(table_name)

            if expression == '=':
                expression = '=='

            exec(f'from zvt.domain import {domain_name}')

            if isinstance(value, str):
                filter_str = '{}.{} {} "{}"'.format(domain_name, col, expression, value)
            else:
                filter_str = '{}.{} {} {}'.format(domain_name, col, expression, value)
            return {'_type': 'filter',
                    'data': filter_str}

        return super().default(obj)


class CustomJsonDecoder(json.JSONDecoder):
    def __init__(self, *args, **kwargs):
        json.JSONDecoder.__init__(self, object_hook=self.object_hook, *args, **kwargs)

    def object_hook(self, obj):
        if '_type' not in obj:
            return obj

        _type = obj.get('_type')
        data = obj.get('data')

        if _type == 'filter':
            filter_str = data

            left, _, _ = filter_str.split()
            domain_name, col = left.split('.')

            exec(f'from zvt.domain import {domain_name}')
            return eval(filter_str)

        return obj
