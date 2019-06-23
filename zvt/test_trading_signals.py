# -*- coding: utf-8 -*-

import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output

from zvt.charts.dcc_components import get_trading_signals_figure
from zvt.domain import TradingLevel
from zvt.reader.business_reader import AccountReader, OrderReader

trader = 'cointrader'
security = 'coin_binance_EOS/USDT'

account_reader = AccountReader(trader_names=['cointrader'], level=TradingLevel.LEVEL_1MIN)
order_reader = OrderReader(trader_names=['cointrader'])


def serve_layout():
    layout = html.Div(
        [
            dcc.Graph(id='{}_trading_signals'.format(security),
                      figure=get_trading_signals_figure(order_reader, security_id=security,
                                                        provider='ccxt',
                                                        level=TradingLevel.LEVEL_1MIN)),
            dcc.Interval(
                id='interval-component',
                interval=10 * 1000,  # in milliseconds
                n_intervals=0
            )
        ])

    return layout


app = dash.Dash(__name__)

app.layout = serve_layout


@app.callback(
    Output('{}_trading_signals'.format(security), 'figure'),
    [Input('interval-component', 'n_intervals')])
def update_trader_details(n):
    # order_reader.move_on()
    return get_trading_signals_figure(order_reader, security_id=security,
                                      provider='ccxt',
                                      level=TradingLevel.LEVEL_1MIN)


if __name__ == '__main__':
    app.run_server(debug=True)
