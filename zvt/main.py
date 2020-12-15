import dash_bootstrap_components as dbc
import dash_html_components as html
from dash.dependencies import Input, Output

from zvt import init_plugins
from zvt.ui import zvt_app
from zvt.ui.apps import factor_app, trader_app


def serve_layout():
    layout = html.Div(
        children=[
            # banner
            html.Div(
                className="zvt-banner",
                children=html.H2(className="h2-title", children="ZVT")
            ),
            dbc.CardHeader(
                dbc.Tabs(
                    [
                        dbc.Tab(label="factor", tab_id="tab-factor", label_style={}, tab_style={"width": "100px"}),
                        dbc.Tab(label="trader", tab_id="tab-trader", label_style={}, tab_style={"width": "100px"}),
                    ],
                    id="card-tabs",
                    card=True,
                    active_tab="tab-factor",
                )
            ),
            dbc.CardBody(html.P(id="card-content", className="card-text")),
        ]
    )

    return layout


@zvt_app.callback(
    Output("card-content", "children"), [Input("card-tabs", "active_tab")]
)
def tab_content(active_tab):
    if 'tab-factor' == active_tab:
        return factor_app.factor_layout()
    elif 'tab-trader' == active_tab:
        return trader_app.trader_layout()


zvt_app.layout = serve_layout


def main():
    init_plugins()
    zvt_app.run_server(debug=True)
    # zvt_app.run_server()


if __name__ == '__main__':
    main()
