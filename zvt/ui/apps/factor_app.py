# -*- coding: utf-8 -*-

import dash_core_components as dcc
import dash_html_components as html
from dash import dash
from dash.dependencies import Input, Output, State

from zvt.contract import Mixin
from zvt.contract import zvt_context, IntervalLevel
from zvt.contract.api import get_entities, get_schema_by_name, get_schema_columns
from zvt.contract.drawer import StackedDrawer
from zvt.ui import zvt_app
from zvt.utils import pd_is_not_null


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
                            # select entity_type
                            html.Div(
                                className="padding-top-bot",
                                children=[
                                    html.H6("select entity type:"),
                                    dcc.Dropdown(id='entity-type-selector',
                                                 placeholder='select entity type',
                                                 options=[{'label': name, 'value': name} for name in
                                                          zvt_context.entity_schema_map.keys()],
                                                 value='stock')
                                ],
                            ),

                            # select code
                            html.Div(
                                className="padding-top-bot",
                                children=[
                                    html.H6("select code:"),
                                    dcc.Dropdown(id='code-selector',
                                                 placeholder='select code')
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
                                    html.H6("select data to show in sub graph:"),
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
                        id='factor-details'
                    )
                ])
        ]
    )

    return layout


@zvt_app.callback(
    [Output('data-selector', 'options'),
     Output('code-selector', 'options')],
    [Input('entity-type-selector', 'value')])
def update_code_selector(entity_type):
    if entity_type is not None:
        return [{'label': schema.__name__, 'value': schema.__name__} for schema in
                zvt_context.entity_map_schemas.get(entity_type)], \
               [{'label': code, 'value': code} for code in
                get_entities(entity_type=entity_type, columns=['code']).index]
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
     Input('code-selector', 'value'),
     Input('levels-selector', 'value'),
     Input('schema-column-selector', 'value')],
    state=[State('data-selector', 'value')])
def update_factor_details(factor, entity_type, code, levels, columns, schema_name):
    if factor and entity_type and code and levels:
        sub_df = None
        if columns:
            if type(columns) == str:
                columns = [columns]
            columns = columns + ['entity_id', 'timestamp']
            schema: Mixin = get_schema_by_name(name=schema_name)
            sub_df = schema.query_data(code=code, columns=columns)
        if type(levels) is list and len(levels) >= 2:
            levels.sort()
            drawers = []
            for level in levels:
                drawers.append(zvt_context.factor_cls_registry[factor](
                    entity_schema=zvt_context.entity_schema_map[entity_type],
                    level=level, codes=[code]).drawer())
            stacked = StackedDrawer(*drawers)

            return dcc.Graph(
                id=f'{factor}-{entity_type}-{code}',
                figure=stacked.draw_kline(show=False, height=900))
        else:
            if type(levels) is list:
                level = levels[0]
            else:
                level = levels
            drawer = zvt_context.factor_cls_registry[factor](entity_schema=zvt_context.entity_schema_map[entity_type],
                                                             level=level,
                                                             codes=[code],
                                                             need_persist=False).drawer()
            if pd_is_not_null(sub_df):
                drawer.add_sub_df(sub_df)

            return dcc.Graph(
                id=f'{factor}-{entity_type}-{code}',
                figure=drawer.draw_kline(show=False, height=800))
    raise dash.PreventUpdate()
