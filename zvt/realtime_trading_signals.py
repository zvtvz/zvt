# -*- coding: utf-8 -*-

import dash
import dash_core_components as dcc
import dash_daq as daq
import dash_html_components as html
from dash.dependencies import Input, Output

from zvt.api.business import get_trader
from zvt.api.technical import get_current_price
from zvt.charts.dcc_components import get_trader_detail_figures
from zvt.domain import TradingLevel
from zvt.reader.business_reader import AccountReader, OrderReader

trader = 'singlecointrader'
security = 'coin_binance_EOS/USDT'

trader_domain = get_trader(trader_name=trader, return_type='domain')[0]
account_reader = AccountReader(trader_names=['singlecointrader'], level=TradingLevel.LEVEL_1MIN)
order_reader = OrderReader(trader_names=['singlecointrader'])


def serve_layout():
    layout = html.Div(
        [
            daq.LEDDisplay(
                id='current_price',
                label="EOS/USDT current price",
                value=get_current_price(security_list=[security]),
                color="#FF5E5E"
            ),

            html.Div(id='trader-details', children=get_trader_detail_figures(trader_domain=trader_domain,
                                                                             account_reader=None,
                                                                             order_reader=order_reader)),

            dcc.Interval(
                id='interval-component',
                interval=20 * 1000,  # in milliseconds
                n_intervals=0
            ),
            dcc.Interval(
                id='interval-component1',
                interval=3 * 1000,  # in milliseconds
                n_intervals=0
            )
        ])

    return layout


app = dash.Dash(__name__)

app.layout = serve_layout


@app.callback(
    Output('trader-details', 'children'),
    [Input('interval-component', 'n_intervals')])
def update_trader_details(n):
    # order_reader.move_on()
    return get_trader_detail_figures(trader_domain=trader_domain,
                                     account_reader=None,
                                     order_reader=order_reader)


@app.callback(
    Output('current_price', 'value'),
    [Input('interval-component1', 'n_intervals')])
def update_current_price(n):
    price_reader.move_on()
    return price_reader.get_data_df()['price'][-1]


if __name__ == '__main__':
    app.run_server(debug=True)
