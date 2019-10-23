# -*- coding: utf-8 -*-

import plotly.graph_objs as go
import simplejson

from zvt.api.common import decode_entity_id
from zvt.api.quote import get_current_price
from zvt.domain import business
from zvt.factors.technical_factor import TechnicalFactor
from zvt.reader.business_reader import OrderReader, AccountReader
from zvdata.utils.pd_utils import pd_is_not_null


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
                               entity_id: str,
                               provider: str,
                               level):
    entity_type, _, _ = decode_entity_id(entity_id)
    security_factor = TechnicalFactor(entity_type=entity_type, entity_ids=[entity_id],
                                      level=level, provider=provider)

    if pd_is_not_null(security_factor.data_df):
        print(security_factor.data_df.tail())

    # generate the annotation df
    order_reader.move_on(timeout=0)
    df = order_reader.data_df.copy()
    if pd_is_not_null(df):
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

    if account_reader:
        account_data, account_layout = account_reader.data_drawer().draw_line(render=None, keep_ui_state=False)

        for trader_name in account_reader.trader_names:
            graph_list.append(dcc.Graph(
                id='{}-account'.format(trader_name),
                figure={
                    'data': account_data,
                    'layout': account_layout
                }))

    order_reader.move_on(timeout=0)
    df_orders = order_reader.data_df.copy()

    if pd_is_not_null(df_orders):
        grouped = df_orders.groupby('entity_id')

        for entity_id, order_df in grouped:
            entity_type, _, _ = decode_entity_id(entity_id)

            indicators = []
            indicators_param = []
            indicator_cols = []
            if trader_domain.technical_factors:
                tech_factors = simplejson.loads(trader_domain.technical_factors)
                print(tech_factors)
                for factor in tech_factors:
                    indicators += factor['indicators']
                    indicators_param += factor['indicators_param']
                    indicator_cols += factor['indicator_cols']

            security_factor = TechnicalFactor(entity_type=entity_type, entity_ids=[entity_id],
                                              start_timestamp=trader_domain.start_timestamp,
                                              end_timestamp=trader_domain.end_timestamp,
                                              level=trader_domain.level, provider=trader_domain.provider,
                                              indicators=indicators,
                                              indicators_param=indicators_param)

            # generate the annotation df
            df = order_df.copy()
            if pd_is_not_null(df):
                df['value'] = df['order_price']
                df['flag'] = df['order_type'].apply(lambda x: order_type_flag(x))
                df['color'] = df['order_type'].apply(lambda x: order_type_color(x))
            print(df.tail())

            data, layout = security_factor.draw_pipe(render=None, annotation_df=df, height=620)
            if trader_domain.real_time:
                result = get_current_price(entity_ids=[entity_id])
                bid_ask = result.get(entity_id)

                if bid_ask:
                    graph_list.append(daq.LEDDisplay(
                        id='ask',
                        label=f'ask price',
                        value=bid_ask[0],
                        color="#00da3c"
                    ))

                    graph_list.append(daq.LEDDisplay(
                        id='bid',
                        label=f'bid price',
                        value=bid_ask[1],
                        color="#FF5E5E"
                    ))

            graph_list.append(
                dcc.Graph(
                    id='{}-{}-signals'.format(trader_domain.trader_name, entity_id),
                    figure={
                        'data': data,
                        'layout': layout
                    }
                )
            )

    return graph_list
