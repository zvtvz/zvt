# -*- coding: utf-8 -*-
from typing import List

import dash_core_components as dcc
import dash_daq as daq
import dash_html_components as html
from dash import dash
from dash.dependencies import Input, Output, State

from zvt.api.trader_info_api import AccountStatsReader, OrderReader, get_order_securities
from zvt.api.trader_info_api import get_trader_info
from zvt.contract import Mixin
from zvt.contract import zvt_context, IntervalLevel
from zvt.contract.api import get_entities, get_schema_by_name, get_schema_columns
from zvt.contract.drawer import StackedDrawer
from zvt.domain import TraderInfo
from zvt.ui import zvt_app
from zvt.ui.components.dcc_components import get_account_stats_figure
from zvt.utils import pd_is_not_null

account_readers = []
order_readers = []

# init the data
traders: List[TraderInfo] = []

trader_names: List[str] = []


def order_type_flag(order_type):
    if order_type == 'order_long' or order_type == 'order_close_short':
        return 'B'
    else:
        return 'S'


def order_type_color(order_type):
    if order_type == 'order_long' or order_type == 'order_close_short':
        return "#ec0000"
    else:
        return "#00da3c"


def load_traders():
    global traders
    global trader_names

    traders = get_trader_info(return_type='domain')
    account_readers.clear()
    order_readers.clear()
    for trader in traders:
        account_readers.append(AccountStatsReader(trader_names=[trader.trader_name], level=trader.level))
        order_readers.append(
            OrderReader(trader_names=[trader.trader_name], level=trader.level, start_timestamp=trader.start_timestamp))

    trader_names = [item.trader_name for item in traders]


load_traders()


def factor_layout():
    layout = html.Div(
        [
            # controls
            html.Div(
                className="three columns card",
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

                            # select entity_type
                            html.Div(
                                className="padding-top-bot",
                                children=[
                                    html.H6("select entity type:"),
                                    dcc.Dropdown(id='entity-type-selector',
                                                 placeholder='select entity type',
                                                 options=[{'label': name, 'value': name} for name in
                                                          zvt_context.entity_schema_map.keys()],
                                                 value='stock',
                                                 clearable=False)
                                ],
                            ),

                            # select entity
                            html.Div(
                                className="padding-top-bot",
                                children=[
                                    html.H6("select entity:"),
                                    dcc.Dropdown(id='entity-selector',
                                                 placeholder='select entity')
                                ],
                            ),
                            # select levels
                            html.Div(
                                className="padding-top-bot",
                                children=[
                                    html.H6("select levels:"),
                                    dcc.Dropdown(
                                        id='levels-selector',
                                        options=[{'label': level.name, 'value': level.value} for level in
                                                 (IntervalLevel.LEVEL_1WEEK, IntervalLevel.LEVEL_1DAY)],
                                        value='1d',
                                        multi=True
                                    )
                                ],
                            ),
                            # select factor
                            html.Div(
                                className="padding-top-bot",
                                children=[
                                    html.H6("select factor:"),
                                    dcc.Dropdown(id='factor-selector',
                                                 placeholder='select factor',
                                                 options=[{'label': name, 'value': name} for name in
                                                          zvt_context.factor_cls_registry.keys()],
                                                 value='TechnicalFactor')
                                ]
                            ),
                            # select data
                            html.Div(
                                children=[
                                    html.Div(
                                        [
                                            html.H6("related/all data to show in sub graph",
                                                    style={"display": "inline-block"}),
                                            daq.BooleanSwitch(
                                                id='data-switch',
                                                on=True,
                                                style={"display": "inline-block",
                                                       "float": "right",
                                                       "vertical-align": "middle",
                                                       "padding": "8px"}
                                            ),
                                        ],
                                    ),
                                    dcc.Dropdown(id='data-selector', placeholder='schema')
                                ],
                                style={"padding-top": "12px"}
                            ),
                            # select properties
                            html.Div(
                                children=[
                                    dcc.Dropdown(id='schema-column-selector', placeholder='properties')
                                ],
                                style={"padding-top": "6px"}
                            ),

                        ])
                ]),
            # Graph
            html.Div(
                className="nine columns card-left",
                children=[
                    html.Div(
                        id='trader-details',
                        className="bg-white",
                    ),
                    html.Div(
                        id='factor-details'
                    )
                ])
        ]
    )

    return layout


@zvt_app.callback(
    [Output('trader-details', 'children'),
     Output('entity-type-selector', 'options'),
     Output('entity-selector', 'options')],
    [Input('trader-selector', 'value'), Input('entity-type-selector', 'value')])
def update_trader_details(trader_index, entity_type):
    if trader_index is not None:
        # change entity_type options
        entity_type = traders[trader_index].entity_type
        if not entity_type:
            entity_type = 'stock'
        entity_type_options = [{'label': entity_type, 'value': entity_type}]

        # account stats
        account_stats = get_account_stats_figure(account_stats_reader=account_readers[trader_index])

        # entities
        entity_ids = get_order_securities(trader_name=trader_names[trader_index])
        df = get_entities(entity_type=entity_type, entity_ids=entity_ids, columns=['entity_id', 'code', 'name'],
                          index='entity_id')
        entity_options = [{'label': f'{entity_id}({entity["name"]})', 'value': entity_id} for entity_id, entity in
                          df.iterrows()]

        return account_stats, entity_type_options, entity_options
    else:
        entity_type_options = [{'label': name, 'value': name} for name in zvt_context.entity_schema_map.keys()]
        account_stats = None
        df = get_entities(entity_type=entity_type, columns=['entity_id', 'code', 'name'], index='entity_id')
        entity_options = [{'label': f'{entity_id}({entity["name"]})', 'value': entity_id} for entity_id, entity in
                          df.iterrows()]
        return account_stats, entity_type_options, entity_options


@zvt_app.callback(
    Output('data-selector', 'options'),
    [Input('entity-type-selector', 'value'), Input('data-switch', 'on')])
def update_entity_selector(entity_type, related):
    if entity_type is not None:
        if related:
            schemas = zvt_context.entity_map_schemas.get(entity_type)
        else:
            schemas = zvt_context.schemas
        return [{'label': schema.__name__, 'value': schema.__name__} for schema in schemas]
    raise dash.PreventUpdate()


@zvt_app.callback(
    Output('schema-column-selector', 'options'),
    [Input('data-selector', 'value')])
def update_column_selector(schema_name):
    if schema_name:
        schema = get_schema_by_name(name=schema_name)
        cols = get_schema_columns(schema=schema)

        return [{'label': col, 'value': col} for col in cols]
    raise dash.PreventUpdate()


@zvt_app.callback(
    Output('factor-details', 'children'),
    [Input('factor-selector', 'value'),
     Input('entity-type-selector', 'value'),
     Input('entity-selector', 'value'),
     Input('levels-selector', 'value'),
     Input('schema-column-selector', 'value')],
    state=[State('trader-selector', 'value'), State('data-selector', 'value')])
def update_factor_details(factor, entity_type, entity, levels, columns, trader_index, schema_name):
    if factor and entity_type and entity and levels:
        sub_df = None
        # add sub graph
        if columns:
            if type(columns) == str:
                columns = [columns]
            columns = columns + ['entity_id', 'timestamp']
            schema: Mixin = get_schema_by_name(name=schema_name)
            sub_df = schema.query_data(entity_id=entity, columns=columns)

        # add trading signals as annotation
        annotation_df = None
        if trader_index is not None:
            order_reader = order_readers[trader_index]
            annotation_df = order_reader.data_df.copy()
            annotation_df = annotation_df[annotation_df.entity_id == entity].copy()
            if pd_is_not_null(annotation_df):
                annotation_df['value'] = annotation_df['order_price']
                annotation_df['flag'] = annotation_df['order_type'].apply(lambda x: order_type_flag(x))
                annotation_df['color'] = annotation_df['order_type'].apply(lambda x: order_type_color(x))
            print(annotation_df.tail())

        if type(levels) is list and len(levels) >= 2:
            levels.sort()
            drawers = []
            for level in levels:
                drawers.append(zvt_context.factor_cls_registry[factor](
                    entity_schema=zvt_context.entity_schema_map[entity_type],
                    level=level, entity_ids=[entity]).drawer())
            stacked = StackedDrawer(*drawers)

            return dcc.Graph(
                id=f'{factor}-{entity_type}-{entity}',
                figure=stacked.draw_kline(show=False, height=900))
        else:
            if type(levels) is list:
                level = levels[0]
            else:
                level = levels
            drawer = zvt_context.factor_cls_registry[factor](entity_schema=zvt_context.entity_schema_map[entity_type],
                                                             level=level,
                                                             entity_ids=[entity],
                                                             need_persist=False).drawer()
            if pd_is_not_null(sub_df):
                drawer.add_sub_df(sub_df)
            if pd_is_not_null(annotation_df):
                drawer.annotation_df = annotation_df

            return dcc.Graph(
                id=f'{factor}-{entity_type}-{entity}',
                figure=drawer.draw_kline(show=False, height=800))
    raise dash.PreventUpdate()
