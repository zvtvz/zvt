# -*- coding: utf-8 -*-

import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output

from zvt.api.business import get_trader
from zvt.charts.dcc_components import get_trader_detail_figures
from zvt.domain import TradingLevel
from zvt.reader.business_reader import AccountReader, OrderReader

account_reader = AccountReader(trader_names=['cointrader'], level=TradingLevel.LEVEL_1MIN)
order_reader = OrderReader(trader_names=['cointrader'])

account_readers = []
order_readers = []

# init the data
trader_domains = get_trader(return_type='domain')
for trader in trader_domains:
    account_readers.append(AccountReader(trader_names=[trader.trader_name], level=trader.level))
    order_readers.append(OrderReader(trader_names=[trader.trader_name]))

trader_names = [item.trader_name for item in trader_domains]


def serve_layout():
    layout = html.Div(
        [html.Div(
            [
                dcc.Dropdown(
                    id='trader-selector',
                    options=[{'label': item, 'value': i} for i, item in enumerate(trader_names)]),

                dcc.Markdown('''
#### trader statistic would coming soon
                ''')
            ], style={'width': '20%', 'display': 'inline-block', 'vertical-align': 'top'}),

            html.Div(id='trader-details', style={'width': '70%', 'display': 'inline-block'}),
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
    Output('trader-details', 'children'),
    [Input('trader-selector', 'value')])
def update_trader_details(i):
    # order_reader.move_on()
    if i is None:
        return html.Div('please select one trader to view')
    return get_trader_detail_figures(trader_domain=trader_domains[i], account_reader=account_readers[i],
                                     order_reader=order_readers[i])


# @app.callback(
#     Output('trader-details', 'children'),
#     [Input('interval-component', 'n_intervals')])
# def update_trader_details(n):
#     # order_reader.move_on()
#     return get_trader_detail_figures(trader_domain=trader_domains[i], account_reader=account_readers[i],
#                                      order_reader=order_readers[i])


if __name__ == '__main__':
    app.run_server(debug=True)
