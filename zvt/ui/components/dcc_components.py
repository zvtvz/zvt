# -*- coding: utf-8 -*-

import dash_core_components as dcc

from zvt.api.quote import decode_entity_id, get_kdata_schema
from zvt.api.trader_info_api import OrderReader, AccountStatsReader
from zvt.contract.drawer import Drawer
from zvt.contract.reader import DataReader
from zvt.contract.zvt_context import entity_schema_map
from zvt.utils.pd_utils import pd_is_not_null


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
                               start_timestamp=None,
                               end_timestamp=None,
                               adjust_type=None):
    entity_type, _, _ = decode_entity_id(entity_id)

    data_schema = get_kdata_schema(entity_type=entity_type, level=order_reader.level, adjust_type=adjust_type)
    if not start_timestamp:
        start_timestamp = order_reader.start_timestamp
    if not end_timestamp:
        end_timestamp = order_reader.end_timestamp
    kdata_reader = DataReader(entity_ids=[entity_id], data_schema=data_schema,
                              entity_schema=entity_schema_map.get(entity_type),
                              start_timestamp=start_timestamp,
                              end_timestamp=end_timestamp,
                              level=order_reader.level)

    # generate the annotation df
    order_reader.move_on(timeout=0)
    df = order_reader.data_df.copy()
    df = df[df.entity_id == entity_id].copy()
    if pd_is_not_null(df):
        df['value'] = df['order_price']
        df['flag'] = df['order_type'].apply(lambda x: order_type_flag(x))
        df['color'] = df['order_type'].apply(lambda x: order_type_color(x))
    print(df.tail())

    drawer = Drawer(main_df=kdata_reader.data_df, annotation_df=df)
    return drawer.draw_kline(show=False, height=800)


def get_account_stats_figure(account_stats_reader: AccountStatsReader):
    graph_list = []

    # 账户统计曲线
    if account_stats_reader:
        fig = account_stats_reader.draw_line(show=False)

        for trader_name in account_stats_reader.trader_names:
            graph_list.append(dcc.Graph(
                id='{}-account'.format(trader_name),
                figure=fig))

    return graph_list
