# -*- coding: utf-8 -*-
import inspect
import json
from enum import Enum

import pandas as pd
import simplejson
from sqlalchemy.ext.declarative import DeclarativeMeta
from sqlalchemy.orm.attributes import InstrumentedAttribute
from sqlalchemy.sql.elements import BinaryExpression

from zvdata.contract import zvdata_env, table_name_to_domain_name
from zvdata.utils.time_utils import to_time_str


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

            exec(f'from {zvdata_env["domain_module"]} import {domain_name}')

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

            exec(f'from {zvdata_env["domain_module"]} import {domain_name}')
            return eval(filter_str)

        return obj


class Jsonable(object):
    def id(self):
        return hash(simplejson.dumps(self.__json__()))

    def __json__(self):
        result = {}

        spec = inspect.getfullargspec(self.__class__)
        args = [arg for arg in spec.args if arg != 'self']
        for arg in args:
            value = eval('self.{}'.format(arg))
            json_value = value

            if isinstance(value, pd.Timestamp):
                json_value = to_time_str(value)

            if isinstance(value.__class__, DeclarativeMeta):
                json_value = value.__class__.__name__

            if isinstance(value, InstrumentedAttribute):
                json_value = value.name

            if isinstance(value, Enum):
                json_value = value.value

            result[arg] = json_value

        return result

    for_json = __json__  # supported by simplejson
