# -*- coding: utf-8 -*-
from typing import List

import pandas as pd


def index_df_with_time(df, index='timestamp', inplace=True, drop=True):
    if inplace:
        df.set_index(index, drop=drop, inplace=inplace)
    else:
        df = df.set_index(index, drop=drop, inplace=inplace)
    df.index = pd.to_datetime(df.index)
    df = df.sort_index()
    return df


def index_df_with_security_time(df):
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df = df.set_index(['security_id', 'timestamp'])
    df.index.names = ['security_id', 'timestamp']
    df = df.sort_index(level=[0, 1])
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
        df1 = df.reindex(idx)
        df1 = df1.sort_index()
        result.append(df1)
    return result
