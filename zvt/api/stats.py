# -*- coding: utf-8 -*-
import itertools
from typing import Union

import pandas as pd

from zvt.api import get_kdata_schema
from zvt.contract import Mixin, AdjustType
from zvt.contract.api import decode_entity_id


def get_top_performance_entities(entity_type='stock', start_timestamp=None, end_timestamp=None, pct=0.1,
                                 return_type='both', adjust_type: Union[AdjustType, str] = None):
    if not adjust_type and entity_type == 'stock':
        adjust_type = AdjustType.hfq
    data_schema = get_kdata_schema(entity_type=entity_type, adjust_type=adjust_type)

    return get_top_entities(data_schema=data_schema, start_timestamp=start_timestamp, end_timestamp=end_timestamp,
                            column='close', pct=pct, method='change', return_type=return_type)


def get_performance(entity_ids, start_timestamp=None, end_timestamp=None, adjust_type: Union[AdjustType, str] = None):
    entity_type, _, _ = decode_entity_id(entity_ids[0])
    if not adjust_type and entity_type == 'stock':
        adjust_type = AdjustType.hfq
    data_schema = get_kdata_schema(entity_type=entity_type, adjust_type=adjust_type)

    result, _ = get_top_entities(data_schema=data_schema, column='close', start_timestamp=start_timestamp,
                                 end_timestamp=end_timestamp, pct=1, method='change', return_type='positive',
                                 filters=[data_schema.entity_id.in_(entity_ids)])
    return result


def get_top_volume_entities(entity_type='stock', start_timestamp=None, end_timestamp=None, pct=0.1,
                            return_type='both', adjust_type: Union[AdjustType, str] = None, method='avg'):
    if not adjust_type and entity_type == 'stock':
        adjust_type = AdjustType.hfq
    data_schema = get_kdata_schema(entity_type=entity_type, adjust_type=adjust_type)

    result, _ = get_top_entities(data_schema=data_schema, start_timestamp=start_timestamp, end_timestamp=end_timestamp,
                                 column='turnover', pct=pct, method=method, return_type=return_type)
    return result


def get_top_entities(data_schema: Mixin, column, start_timestamp=None, end_timestamp=None, pct=0.1, method='change',
                     return_type='both', filters=None):
    all_df = data_schema.query_data(start_timestamp=start_timestamp, end_timestamp=end_timestamp,
                                    columns=['entity_id', column], filters=filters)
    g = all_df.groupby('entity_id')
    tops = {}
    for entity_id, df in g:
        if method == 'change':
            start = df[column].iloc[0]
            end = df[column].iloc[-1]
            change = (end - start) / start
            tops[entity_id] = change
        elif method == 'avg':
            tops[entity_id] = df[column].mean()
        elif method == 'sum':
            tops[entity_id] = df[column].sum()

    positive_df = None
    negative_df = None
    top_index = int(len(tops) * pct)
    if return_type == 'positive' or return_type == 'both':
        # from big to small
        positive_tops = {k: v for k, v in sorted(tops.items(), key=lambda item: item[1], reverse=True)}
        positive_tops = dict(itertools.islice(positive_tops.items(), top_index))
        positive_df = pd.DataFrame.from_dict(positive_tops, orient='index')

        col = 'score'
        positive_df.columns = [col]
        positive_df.sort_values(by=col, ascending=False)
    if return_type == 'negative' or return_type == 'both':
        # from small to big
        negative_tops = {k: v for k, v in sorted(tops.items(), key=lambda item: item[1])}
        negative_tops = dict(itertools.islice(negative_tops.items(), top_index))
        negative_df = pd.DataFrame.from_dict(negative_tops, orient='index')

        col = 'score'
        negative_df.columns = [col]
        negative_df.sort_values(by=col)

    return positive_df, negative_df


if __name__ == '__main__':
    from pprint import pprint

    tops1, tops2 = get_top_performance_entities(start_timestamp='2020-01-01')

    pprint(tops1)
    pprint(tops2)
# the __all__ is generated
__all__ = ['get_top_performance_entities', 'get_performance', 'get_top_volume_entities', 'get_top_entities']
