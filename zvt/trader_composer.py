# -*- coding: utf-8 -*-
from multiprocessing import Process

import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State

from zvt.charts.dcc_components import get_trader_detail_figures
from zvt.charts.html_components import cls_to_input_list
from zvt.composer import get_trader_classes
from zvt.reader.business_reader import AccountReader, OrderReader
from zvt.trader.examples import CoinTrader


def run_trader(trader):
    trader.run()


def process_run(trader):
    p = Process(target=run_trader, args=(trader,))
    p.start()


account_readers = {}
order_readers = {}

app = dash.Dash(__name__)

# app.config['suppress_callback_exceptions'] = True

traders = get_trader_classes()

constructor_divs, constructor_states = cls_to_input_list(CoinTrader)


def serve_layout():
    layout = html.Div(
        [  # left
            html.Div([html.Div([html.Label('select trader:'),
                                dcc.Dropdown(
                                    id='trader_selector',
                                    options=[{'label': trader[0], 'value': i} for i, trader in
                                             enumerate(traders)],
                                    value=0)
                                ]),
                      html.Div(id='trader_constructor', children=constructor_divs),
                      html.Button('run the trader', id='btn_run_trader', n_clicks_timestamp=0),
                      html.Div(id='trader_index', style={'display': 'none'})
                      ],
                     style={'width': '20%', 'display': 'inline-block'}),
            # right
            html.Div(id='trader_status',
                     style={'width': '10%', 'display': 'inline-block'}),
            # right
            html.Div(id='trader_details',
                     style={'width': '50%', 'display': 'inline-block'}),
            dcc.Interval(
                id='interval-component',
                interval=10 * 1000,  # in milliseconds
                n_intervals=0
            )
        ]
    )

    return layout


app.layout = serve_layout


@app.callback(
    [Output('trader_constructor', 'children'),
     Output('trader_index', 'children')],
    [Input('trader_selector', 'value')])
def update_trader_constructor(trader_class_index):
    divs, _ = cls_to_input_list(traders[trader_class_index][1])
    return divs, trader_class_index


@app.callback(
    Output('trader_status', 'children'),
    [Input('btn_run_trader', 'n_clicks')],
    constructor_states + [State('trader_index', 'children')])
def update_trader_status(n_clicks, security_list, exchanges, codes, start_timestamp, end_timestamp, provider, level,
                         trader_name, real_time, kdata_use_begin_time, trader_index):
    if n_clicks and (trader_index is not None):
        if trader_name not in account_readers:
            trader = traders[trader_index][1](security_list, exchanges, codes, start_timestamp, end_timestamp, provider,
                                              level, trader_name, real_time, kdata_use_begin_time)
            process_run(trader)
            account_readers[trader.trader_name] = AccountReader(trader_names=[trader.trader_name], level=trader.level)
            order_readers[trader.trader_name] = OrderReader(trader_names=[trader.trader_name])

            return html.Label('trader is running'.format(trader_name))

    return html.Label('trader status')


@app.callback(Output('trader_details', 'children'),
              [Input('interval-component', 'n_intervals')],
              [State('trader_name', 'value')])
def update_trader_details(n, trader_name):
    if trader_name is not None:
        if trader_name in account_readers:
            account_readers[trader_name].move_on(timeout=1)
            order_readers[trader_name].move_on(timeout=1)
            return get_trader_detail_figures(account_readers[trader_name], order_readers[trader_name])
    return html.Label('trader details')


if __name__ == '__main__':
    app.run_server(debug=True)
