# -*- coding: utf-8 -*-
from typing import List

import pandas as pd

from zvt.api.kdata import get_kdata_schema
from zvt.contract.api import decode_entity_id
from zvt.contract.drawer import Drawer, ChartType
from zvt.utils import to_pd_timestamp


def compare(entity_ids, schema_map_columns: dict = None, chart_type: ChartType = ChartType.line):
    entity_type_map_ids = _group_entity_ids(entity_ids=entity_ids)
    dfs = []
    for entity_type in entity_type_map_ids:
        if schema_map_columns:
            for schema in schema_map_columns:
                columns = ["entity_id", "timestamp"] + schema_map_columns.get(schema)
                df = schema.query_data(entity_ids=entity_type_map_ids.get(entity_type), columns=columns)
                dfs.append(df)
        else:
            schema = get_kdata_schema(entity_type=entity_type)
            df = schema.query_data(entity_ids=entity_type_map_ids.get(entity_type))
            dfs.append(df)
    all_df = pd.concat(dfs)

    if schema_map_columns:
        drawer = Drawer(main_df=all_df)
        drawer.draw(main_chart=chart_type, show=True)
    else:
        drawer = Drawer(main_df=all_df, sub_df_list=[all_df[["entity_id", "timestamp", "turnover"]].copy()])
        drawer.draw_kline(show=True)


def distribute(entity_ids, data_schema, columns, histnorm="percent", nbinsx=20, filters=None):
    columns = ["entity_id", "timestamp"] + columns
    df = data_schema.query_data(entity_ids=entity_ids, columns=columns, filters=filters)
    if not entity_ids:
        df["entity_id"] = "entity_x_distribute"
    drawer = Drawer(main_df=df)
    drawer.draw_histogram(show=True, histnorm=histnorm, nbinsx=nbinsx)


def composite(entity_id, data_schema, columns, filters=None):
    columns = ["entity_id", "timestamp"] + columns
    df = data_schema.query_data(entity_id=entity_id, columns=columns, filters=filters)
    drawer = Drawer(main_df=df)
    drawer.draw_pie(show=True)


def composite_all(data_schema, column, timestamp, entity_ids=None, filters=None):
    if type(column) is not str:
        column = column.name
    if filters:
        filters.append([data_schema.timestamp == to_pd_timestamp(timestamp)])
    else:
        filters = [data_schema.timestamp == to_pd_timestamp(timestamp)]
    df = data_schema.query_data(
        entity_ids=entity_ids, columns=["entity_id", "timestamp", column], filters=filters, index="entity_id"
    )
    entity_type, exchange, _ = decode_entity_id(df["entity_id"].iloc[0])
    pie_df = pd.DataFrame(columns=df.index, data=[df[column].tolist()])
    pie_df["entity_id"] = f"{entity_type}_{exchange}_{column}"
    pie_df["timestamp"] = timestamp

    drawer = Drawer(main_df=pie_df)
    drawer.draw_pie(show=True)


def _group_entity_ids(entity_ids):
    entity_type_map_ids = {}
    for entity_id in entity_ids:
        entity_type, _, _ = decode_entity_id(entity_id)
        ids: List = entity_type_map_ids.setdefault(entity_type, [])
        ids.append(entity_id)
    return entity_type_map_ids


if __name__ == "__main__":
    from zvt.domain import CashFlowStatement

    composite(
        entity_id="stock_sz_000338",
        data_schema=CashFlowStatement,
        columns=[
            CashFlowStatement.net_op_cash_flows,
            CashFlowStatement.net_investing_cash_flows,
            CashFlowStatement.net_financing_cash_flows,
        ],
        filters=[
            CashFlowStatement.report_period == "year",
            CashFlowStatement.report_date == to_pd_timestamp("2015-12-31"),
        ],
    )
# the __all__ is generated
__all__ = ["compare", "distribute", "composite", "composite_all"]
