# -*- coding: utf-8 -*-
from typing import Union

import dash_core_components as dcc
import plotly.graph_objs as go

from zvt.api.common import decode_security_id
from zvt.domain import Provider, business
from zvt.factors.technical_factor import TechnicalFactor
from zvt.reader.business_reader import OrderReader, AccountReader
from zvt.utils.pd_utils import df_is_not_null


def get_account_figure(account_reader: AccountReader):
    account_data, account_layout = account_reader.draw(render=None, value_fields='all_value')

    return go.Figure(data=account_data, layout=account_layout)


# ORDER_TYPE_LONG = 'order_long'
# ORDER_TYPE_SHORT = 'order_short'
# ORDER_TYPE_CLOSE_LONG = 'order_close_long'
# ORDER_TYPE_CLOSE_SHORT = 'order_close_short'
def order_type_color(order_type):
    if order_type == 'order_long' or order_type == 'order_close_short':
        return "#ec0000"
    else:
        return "#00da3c"


def order_type_flag(order_type):
    if order_type == 'order_long' or order_type == 'order_close_short':
        return 'B'
    else:
        return 'S'


def get_trading_signals_figure(order_reader: OrderReader,
                               security_id: str,
                               provider: Union[str, Provider],
                               level):
    security_type, _, _ = decode_security_id(security_id)
    security_factor = TechnicalFactor(security_type=security_type, security_list=[security_id],
                                      level=level, provider=provider)

    if df_is_not_null(security_factor.get_data_df()):
        print(security_factor.get_data_df().tail())

    # generate the annotation df
    order_reader.move_on(timeout=0)
    df = order_reader.get_data_df().copy()
    if df_is_not_null(df):
        df['value'] = df['order_price']
        df['flag'] = df['order_type'].apply(lambda x: order_type_flag(x))
        df['color'] = df['order_type'].apply(lambda x: order_type_color(x))
    print(df.tail())

    data, layout = security_factor.draw(render=None, figures=go.Candlestick, annotation_df=df)

    return go.Figure(data=data, layout=layout)


def get_trader_detail_figures(trader_domain: business.Trader,
                              account_reader: AccountReader,
                              order_reader: OrderReader):
    graph_list = []

    account_data, account_layout = account_reader.draw(render=None, value_fields=['all_value'], keep_ui_state=False)

    for trader_name in account_reader.trader_names:
        graph_list.append(dcc.Graph(
            id='{}-account'.format(trader_name),
            figure={
                'data': account_data,
                'layout': account_layout
            }))

    df_orders = order_reader.get_data_df()

    if df_is_not_null(df_orders):
        grouped = df_orders.groupby('security_id')

        for security_id, order_df in grouped:
            security_type, _, _ = decode_security_id(security_id)
            # TODO:just show the indicators used by the trader
            security_factor = TechnicalFactor(security_type=security_type, security_list=[security_id],
                                              start_timestamp=trader_domain.start_timestamp,
                                              end_timestamp=trader_domain.end_timestamp,
                                              level=trader_domain.level, provider=trader_domain.provider,
                                              indicators=['ma', 'ma'],
                                              indicators_param=[{'window': 5}, {'window': 10}]
                                              )

            # if df_is_not_null(security_factor.get_data_df()):
            #     print(security_factor.get_data_df().tail())

            # generate the annotation df
            order_reader.move_on(timeout=0)
            df = order_reader.get_data_df().copy()
            if df_is_not_null(df):
                df['value'] = df['order_price']
                df['flag'] = df['order_type'].apply(lambda x: order_type_flag(x))
                df['color'] = df['order_type'].apply(lambda x: order_type_color(x))
            print(df.tail())

            data, layout = security_factor.draw_with_indicators(render=None, annotation_df=df)

            graph_list.append(
                dcc.Graph(
                    id='{}-{}-signals'.format(trader_domain.trader_name, security_id),
                    figure={
                        'data': data,
                        'layout': layout
                    }
                )
            )

    return graph_list
