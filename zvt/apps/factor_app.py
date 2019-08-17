# -*- coding: utf-8 -*-
import dash_core_components as dcc
import dash_html_components as html
from dash import dash
from dash.dependencies import Input, Output

from zvdata.factor import factor_cls_registry, Factor
from zvdata.sedes import UiComposable
from zvt.app import app


def generate_composer_id(factor_name):
    return f'composer_{factor_name}'


def generate_btn_id(factor_name):
    return f'btn_run_factor_{factor_name}'


def generate_factor_details_id(factor_name):
    return f'factor_details_{factor_name}'


layout = html.Div(
    [
        html.Div(
            [
                # factor selector
                dcc.Dropdown(
                    id='factor_selector',
                    options=[{'label': name, 'value': name} for name, _ in
                             factor_cls_registry.items()]),
                # factor constructor
                html.Div(id='factor_constructor', children=None),
                # factor details
                html.Div([
                    html.Div(
                        id=generate_factor_details_id(factor_name),
                        children=[]) for factor_name, _ in
                    factor_cls_registry.items()]
                ),
            ])
    ]
)


def generate_factor_composer(factor_name):
    cls: UiComposable = factor_cls_registry.get(factor_name)
    inputs, _ = cls.to_html_inputs()

    composer_body = html.Div(
        [
            html.Div(inputs),
        ],
        className='modal-body'
    )

    composer_layout = html.Div(
        [
            html.Div(
                [html.H3(f'construct {factor_name}')],
                className="modal-header"
            ),

            composer_body,

            html.Div(
                [
                    html.Button('run the factor', id=generate_btn_id(factor_name), n_clicks_timestamp=0)
                ],
                className='modal-footer'
            )
        ],
        id=generate_composer_id(factor_name),
        className='modal-content'
    )

    return composer_layout


def hide_composer(n_clicks):
    if n_clicks:
        return {'display': 'none'}


def generate_factor_details_callback(factor_name):
    def update_factor_details(n_clicks, *args):
        if n_clicks:
            factor_cls: Factor = factor_cls_registry.get(factor_name)
            factor_args = factor_cls.from_html_inputs(*args)
            factor: Factor = factor_cls(*factor_args)
            factor.load_data()

            factor_data, factor_layout = factor.draw_depth(render=None)

            return dcc.Graph(
                id=f'{factor_name}_draw_{factor.id()}',
                figure={
                    'data': factor_data,
                    'layout': factor_layout
                }
            )

    return update_factor_details


factor_cls: Factor

for factor_name, factor_cls in factor_cls_registry.items():
    _, states = factor_cls.to_html_inputs()
    app.callback(output=Output(generate_factor_details_id(factor_name), 'children'),
                 inputs=[Input(generate_btn_id(factor_name), 'n_clicks')],
                 state=states)(
        generate_factor_details_callback(factor_name)
    )

    app.callback(output=Output(generate_composer_id(factor_name), 'style'),
                 inputs=[Input(generate_btn_id(factor_name), 'n_clicks')])(
        hide_composer
    )


@app.callback(
    Output('factor_constructor', 'children'),
    [Input('factor_selector', 'value')])
def update_factor_constructor(name):
    if name:
        return generate_factor_composer(factor_name=name)

    raise dash.exceptions.PreventUpdate()
