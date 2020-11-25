# -*- coding: utf-8 -*-

import dash_core_components as dcc
import dash_html_components as html
from dash import dash
from dash.dependencies import Input, Output

from zvt.contract import zvt_context, IntervalLevel
from zvt.contract.api import get_entities
from zvt.contract.drawer import StackedDrawer
from zvt.ui import zvt_app


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
                            # select factor
                            html.Div(
                                className="padding-top-bot",
                                children=[
                                    html.H6("select factor:"),
                                    dcc.Dropdown(id='factor-selector',
                                                 placeholder='select factor',
                                                 options=[{'label': name, 'value': name} for name in
                                                          zvt_context.factor_cls_registry.keys()],
                                                 value='ZenFactor')
                                ]
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
                            )
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
    Output('code-selector', 'options'),
    [Input('entity-type-selector', 'value')])
def update_code_selector(entity_type):
    if entity_type is not None:
        return [{'label': code, 'value': code} for code in
                get_entities(entity_type=entity_type, columns=['code']).index]
    raise dash.PreventUpdate()


@zvt_app.callback(
    Output('factor-details', 'children'),
    [Input('factor-selector', 'value'),
     Input('entity-type-selector', 'value'),
     Input('code-selector', 'value'),
     Input('levels-selector', 'value')])
def update_factor_details(factor, entity_type, code, levels):
    if factor and entity_type and code:
        if type(levels) is list:
            levels.sort(reverse=True)
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
            return dcc.Graph(
                id=f'{factor}-{entity_type}-{code}',
                figure=zvt_context.factor_cls_registry[factor](entity_schema=zvt_context.entity_schema_map[entity_type],
                                                               level=levels,
                                                               codes=[code]).draw(show=False, height=600))
    raise dash.PreventUpdate()
