# -*- coding: utf-8 -*-
import inspect
import json
from enum import Enum

import dash_core_components as dcc
import dash_daq as daq
import dash_html_components as html
import pandas as pd
import simplejson
from dash.dependencies import State
from sqlalchemy.ext.declarative import DeclarativeMeta
from sqlalchemy.orm.attributes import InstrumentedAttribute
from sqlalchemy.sql.elements import BinaryExpression

from zvdata.domain import context, table_name_to_domain_name
from zvdata.structs import IntervalLevel
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

            exec(f'from {context["domain_module"]} import {domain_name}')

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

            exec(f'from {context["domain_module"]} import {domain_name}')
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


class UiComposable(object):
    @classmethod
    def to_html_inputs(cls):
        """
        construct ui input from the class constructor arguments spec

        """
        spec = inspect.getfullargspec(cls)
        args = [arg for arg in spec.args if arg != 'self']
        annotations = spec.annotations
        defaults = [cls.marshal_data_for_ui(default) for default in spec.defaults]

        divs = []
        states = []
        for i, arg in enumerate(args):
            left = html.Label(arg, style={'display': 'inline-block', 'width': '100px'})

            annotation = annotations.get(arg)
            default = defaults[i]

            if annotation is bool:
                right = daq.BooleanSwitch(id=arg, on=default)
                state = State(arg, 'value')
            elif 'level' == arg:
                right = dcc.Dropdown(id=arg,
                                     options=[{'label': item.value, 'value': item.value} for item in IntervalLevel],
                                     value=default)
                state = State(arg, 'value')

            elif 'timestamp' in arg:
                right = dcc.DatePickerSingle(id=arg, date=default)
                state = State(arg, 'date')
            else:
                if 'filters' == arg and default:
                    default = json.dumps(default, cls=CustomJsonDecoder)

                if 'columns' == arg and default:
                    columns = [column.name for column in default]
                    default = ','.join(columns)

                if isinstance(default, list) or isinstance(default, dict):
                    default = json.dumps(default)

                right = dcc.Input(id=arg, type='text', value=default)
                state = State(arg, 'value')

            right.style = {'display': 'inline-block'}
            divs.append(html.Div([left, right], style={'margin-left': '120px'}))
            states.append(state)

        return divs, states

    @classmethod
    def ui_meta(cls):
        return {}

    @classmethod
    def marshal_data_for_ui(cls, data):
        if isinstance(data, Enum):
            return data.value

        if isinstance(data, pd.Timestamp):
            return to_time_str(data)

        return data

    @classmethod
    def unmarshal_data_for_arg(cls, data):
        return data

    @classmethod
    def from_html_inputs(cls, *inputs):
        arg_values = []

        spec = inspect.getfullargspec(cls)
        args = [arg for arg in spec.args if arg != 'self']
        annotations = spec.annotations

        for i, input in enumerate(inputs):
            result = input

            arg = args[i]
            if input:
                try:
                    result = json.loads(input, cls=CustomJsonDecoder)
                except:
                    pass

            arg_values.append(result)

        return arg_values
