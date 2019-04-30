# -*- coding: utf-8 -*-
import pandas as pd


def index_df_with_time(df, index='timestamp'):
    df = df.set_index(df[index], drop=False)
    df.index = pd.to_datetime(df.index)
    df = df.sort_index()
    return df


def index_df_with_security_time(df):
    df.timestamp = pd.to_datetime(df.timestamp)
    df = df.set_index(['security_id', 'timestamp'])
    df.index.names = ['security_id', 'timestamp']
    df = df.sort_index(level=[0, 1])
    return df


def df_subset(df, columns=None):
    if columns:
        return df.loc[:, columns]
    return df
