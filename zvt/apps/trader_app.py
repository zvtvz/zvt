# -*- coding: utf-8 -*-
from typing import List

import dash_core_components as dcc
import dash_html_components as html
from dash import dash
from dash.dependencies import Input, Output, State

from zvt.api.business import get_trader_info, get_order_securities
from zvt.api.business_reader import AccountStatsReader, OrderReader
from zvt.app import app
from zvt.domain import TraderInfo
from zvt.drawer.dcc_components import get_account_stats_figure, get_trading_signals_figure
from zvt.utils.time_utils import TIME_FORMAT_DAY, now_pd_timestamp

account_readers = []
order_readers = []

# init the data
traders: List[TraderInfo] = []

trader_names: List[str] = []


def load_traders():
    global traders
    global trader_names

    traders = get_trader_info(return_type='domain')
    for trader in traders:
        account_readers.append(AccountStatsReader(trader_names=[trader.trader_name], level=trader.level))
        order_readers.append(
            OrderReader(trader_names=[trader.trader_name], level=trader.level, start_timestamp=trader.start_timestamp,
                        end_timestamp=trader.end_timestamp))

    trader_names = [item.trader_name for item in traders]


load_traders()


def serve_layout():
    layout = html.Div(
        children=[
            dcc.Interval(
                id='interval-component',
                interval=60 * 60 * 1000,  # in milliseconds
                n_intervals=0
            ),
            # Top banner
            html.Div(
                className="zvt-banner row",
                children=[
                    html.H2(className="h2-title", children="ZVT"),
                    html.H2(className="h2-title-mobile", children="ZVT"),
                ],
            ),
            # trader body
            html.Div(
                className="row app-body",
                children=[
                    # controls
                    html.Div(
                        className="four columns card",
                        children=[
                            html.Div(
                                className="bg-white user-control",
                                children=[
                                    html.Div(
                                        className="padding-top-bot",
                                        children=[
                                            html.H6("select trader:"),
                                            dcc.Dropdown(id='trader-selector',
                                                         placeholder='select the trader',
                                                         options=[{'label': item, 'value': i} for i, item in
                                                                  enumerate(trader_names)]
                                                         ),
                                        ],
                                    ),
                                    html.Div(
                                        className="padding-top-bot",
                                        children=[
                                            html.H6("select trading target:"),
                                            dcc.Dropdown(id='target-selector',
                                                         placeholder='select the target'
                                                         ),
                                        ],
                                    ),

                                    html.Div(
                                        className="padding-top-bot",
                                        children=[
                                            # time range filter
                                            dcc.DatePickerRange(
                                                id='date-picker-range',
                                                start_date='2009-01-01',
                                                end_date=now_pd_timestamp(),
                                                display_format=TIME_FORMAT_DAY
                                            )
                                        ],
                                    ),
                                ],
                            )
                        ],
                    ),

                    # Graph
                    html.Div(
                        className="eight columns card-left",
                        children=[
                            html.Div(
                                id='trader-details',
                                className="bg-white",
                            ),
                            html.Div(
                                id='target-signals',
                                className="bg-white",
                            )
                        ],
                    )
                ])])

    load_traders()

    return layout


@app.callback(
    [Output('trader-details', 'children'),
     Output('target-selector', 'options'),
     Output('date-picker-range', 'start_date'),
     Output('date-picker-range', 'end_date')],
    [Input('interval-component', 'n_intervals'),
     Input('trader-selector', 'value')])
def update_trader_details(interval, trader_index):
    if trader_index is not None:
        return get_account_stats_figure(account_stats_reader=account_readers[trader_index]), \
               [{'label': security_id, 'value': security_id} for security_id in
                get_order_securities(trader_name=trader_names[trader_index])], \
               traders[trader_index].start_timestamp, \
               traders[trader_index].end_timestamp
    raise dash.exceptions.PreventUpdate()


@app.callback(
    Output('target-signals', 'children'),
    [Input('target-selector', 'value'),
     Input('date-picker-range', 'start_date'),
     Input('date-picker-range', 'end_date')],
    state=[State('trader-selector', 'value')])
def update_target_signals(entity_id, start_date, end_date, trader_index):
    if entity_id and (trader_index is not None):
        return dcc.Graph(
            id=f'{entity_id}-signals',
            figure=get_trading_signals_figure(order_reader=order_readers[trader_index], entity_id=entity_id,
                                              start_timestamp=start_date, end_timestamp=end_date))
    raise dash.exceptions.PreventUpdate()
