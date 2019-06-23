# -*- coding: utf-8 -*-

import dash_core_components as dcc
import dash_daq as daq
import dash_html_components as html
from dash.dependencies import State

from zvt.api.technical import get_securities
from zvt.composer import get_class_constructor_meta
from zvt.domain import SecurityType, COIN_EXCHANGES, COIN_PAIRS, Stock, TradingLevel
from zvt.trader.examples import CoinTrader


def html_label_input_list(args, annotations, defaults, metas):
    divs = []
    states = []
    for i, label in enumerate(args):
        left = html.Label(label)
        if label == 'exchanges':
            right = get_exchanges_input(id=label, security_type=metas['security_type'], default=defaults[i])
            states.append(State(label, 'value'))
        elif label == 'codes':
            right = get_codes_input(id=label, security_type=metas['security_type'])
            states.append(State(label, 'value'))
        elif label in ['the_timestamp', 'start_timestamp', 'end_timestamp']:
            right = get_timestamp_input(id=label, default=defaults[i])
            states.append(State(label, 'date'))
        elif label == 'level':
            right = get_level_input(id=label, default=defaults[i])
            states.append(State(label, 'value'))
        elif annotations.get(label) is bool:
            right = daq.BooleanSwitch(id=label, on=defaults[i])
            states.append(State(label, 'on'))
        else:
            right = dcc.Input(id=label, type='text', value=defaults[i])
            states.append(State(label, 'value'))

        divs += [left, right]

    return divs, states


def get_security_type_input(default='stock', id=None):
    return dcc.Dropdown(id=id, options=[{'label': item.value, 'value': item.value} for item in SecurityType],
                        value=default)


def get_exchanges_input(security_type='stock', default=['sh', 'sz'], id=None):
    if security_type == 'stock':
        exchanges = ['sh', 'sz']

    if security_type == 'coin':
        exchanges = COIN_EXCHANGES

    return dcc.Dropdown(id=id, options=[{'label': item, 'value': item} for item in exchanges],
                        value=default,
                        multi=True)


def get_codes_input(security_type='stock', id=None):
    if security_type == 'stock':
        df = get_securities(security_type=security_type, columns=[Stock.code])
        codes = df['code'].tolist()

    if security_type == 'coin':
        codes = COIN_PAIRS

    return dcc.Dropdown(id=id, options=[{'label': item, 'value': item} for item in codes],
                        value=None,
                        multi=True)


def get_level_input(id=None, default=None):
    return dcc.Dropdown(id=id, options=[{'label': item.value, 'value': item.value} for item in TradingLevel],
                        value=default)


def get_timestamp_input(id=None, default=None):
    return dcc.DatePickerSingle(id=id, date=default)


def cls_to_input_list(cls):
    meta = get_class_constructor_meta(cls)
    return html_label_input_list(args=meta.args, annotations=meta.annotations, defaults=meta.defaults, metas=meta.metas)


if __name__ == '__main__':
    print(cls_to_input_list(CoinTrader))
