# -*- coding: utf-8 -*-
from typing import List

import pandas as pd

from zvt.api import get_kdata_schema
from zvt.contract.api import decode_entity_id
from zvt.contract.drawer import Drawer, ChartType
from zvt.domain import Block, BlockCategory, Block1dKdata
from zvt.utils import to_pd_timestamp


def compare(entity_ids, columns=None, chart_type: ChartType = ChartType.line):
    entity_type_map_ids = _group_entity_ids(entity_ids=entity_ids)
    # compare kdata
    if columns is None:
        dfs = []
        for entity_type in entity_type_map_ids:
            schema = get_kdata_schema(entity_type=entity_type)
            df = schema.query_data(entity_ids=entity_type_map_ids.get(entity_type))
            dfs.append(df)
        all_df = pd.concat(dfs)
        drawer = Drawer(main_df=all_df, sub_df_list=[all_df[['entity_id', 'timestamp', 'turnover']].copy()])
        drawer.draw_kline(main_chart=chart_type, show=True)


def distribute(entity_ids, data_schema, columns, histnorm='percent', nbinsx=20, filters=None):
    df = data_schema.query_data(entity_ids=entity_ids, columns=columns, filters=filters)
    drawer = Drawer(main_df=df)
    drawer.draw_histogram(show=True, histnorm=histnorm, nbinsx=nbinsx)


def composite(entity_id, data_schema, columns, filters=None):
    df = data_schema.query_data(entity_id=entity_id, columns=columns, filters=filters)
    drawer = Drawer(main_df=df)
    drawer.draw_pie(show=True)


def composite_at_time(entity_ids, data_schema, column, timestamp, filters=None):
    if filters:
        filters.append([data_schema.timestamp == to_pd_timestamp(timestamp)])
    else:
        filters = [data_schema.timestamp == to_pd_timestamp(timestamp)]
    df = data_schema.query_data(entity_ids=entity_ids, columns=['name', column], filters=filters, index='name')

    entity_type, exchange, _ = decode_entity_id(entity_ids[0])
    pie_df = pd.DataFrame(columns=df.index, data=[df[column].tolist()])
    pie_df['entity_id'] = f'{entity_type}_{exchange}_{column}'
    pie_df['timestamp'] = timestamp

    drawer = Drawer(main_df=pie_df)
    drawer.draw_pie(show=True)


def _group_entity_ids(entity_ids):
    entity_type_map_ids = {}
    for entity_id in entity_ids:
        entity_type, _, _ = decode_entity_id(entity_id)
        ids: List = entity_type_map_ids.setdefault(entity_type, [])
        ids.append(entity_id)
    return entity_type_map_ids


if __name__ == '__main__':
    df = Block.query_data(filters=[Block.category == BlockCategory.industry.value], index='entity_id')
    entity_ids = df.index.tolist()
    print(entity_ids)
    # Block1dKdata.record_data(entity_ids=entity_ids)
    composite_at_time(entity_ids=entity_ids, data_schema=Block1dKdata, column='turnover', timestamp='2021-09-29')
    compare(entity_ids=entity_ids, data_schema=Block1dKdata, column='turnover_rate', timestamp='2021-09-29')
