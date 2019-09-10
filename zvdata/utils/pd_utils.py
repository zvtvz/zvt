# -*- coding: utf-8 -*-
from typing import List

import pandas as pd


def df_is_not_null(df: pd.DataFrame):
    return df is not None and isinstance(df, pd.DataFrame) and not df.empty


def se_is_not_null(se: pd.Series):
    return se is not None and isinstance(se, pd.Series) and not se.empty


def index_df(df, index='timestamp', inplace=True, drop=True, index_is_time=True):
    if inplace:
        df.set_index(index, drop=drop, inplace=inplace)
    else:
        df = df.set_index(index, drop=drop, inplace=inplace)

    if index_is_time:
        df.index = pd.to_datetime(df.index)
    df = df.sort_index()
    return df


def index_df_with_category_xfield(df, category_field='entity_id', xfield='timestamp', is_timeseries=True):
    if xfield and is_timeseries:
        df[xfield] = pd.to_datetime(df[xfield])

    if xfield:
        df = df.set_index([category_field, xfield])
        df.index.names = [category_field, xfield]
        df = df.sort_index(level=[0, 1])
    else:
        df = df.set_index(category_field)
        df = df.sort_index()
    return df


def df_subset(df, columns=None):
    if columns:
        return df.loc[:, columns]
    return df


def fill_with_same_index(df_list: List[pd.DataFrame]):
    idx = None
    for df in df_list:
        if idx is None:
            idx = df.index
        else:
            idx = idx.append(df.index).drop_duplicates()
    idx = idx.sort_values()

    result = []
    for df in df_list:
        # print(df[df.index.duplicated()])
        added_index = idx.difference(df.index.drop_duplicates())
        added_df = pd.DataFrame(index=added_index, columns=df.columns)

        # df1 = df.reindex(idx)
        df1 = df.append(added_df)
        df1 = df1.sort_index()
        result.append(df1)
    return result
