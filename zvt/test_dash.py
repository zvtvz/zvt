# -*- coding: utf-8 -*-

import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output

from zvt.charts.dcc_components import get_trader_detail_figures
from zvt.domain import TradingLevel
from zvt.reader.business_reader import AccountReader, OrderReader

trader = 'cointrader'

account_reader = AccountReader(trader_names=['cointrader'], level=TradingLevel.LEVEL_1MIN)
order_reader = OrderReader(trader_names=['cointrader'])


def serve_layout():
    layout = html.Div(
        [
            html.Div(id='content'),
            dcc.Interval(
                id='interval-component',
                interval=10 * 1000,  # in milliseconds
                n_intervals=0
            )
        ])

    return layout


app = dash.Dash(__name__)

app.layout = serve_layout


@app.callback(Output('content', 'children'),
              [Input('interval-component', 'n_intervals')])
def update_trader_details(n):
    account_reader.move_on()
    order_reader.move_on()
    return html.Div(get_trader_detail_figures(account_reader, order_reader, provider='ccxt'))


if __name__ == '__main__':
    app.run_server(debug=True)
