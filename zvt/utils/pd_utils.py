# -*- coding: utf-8 -*-
from typing import List, Union

import pandas as pd


def drop_continue_duplicate(s: Union[pd.Series, pd.DataFrame], col=None):
    if type(s) == pd.Series:
        return s[s.shift() != s]
    if type(s) == pd.DataFrame:
        ss = s[col]
        selected = ss[ss.shift() != ss]
        return s.loc[selected.index, :]


def is_filter_result_df(df: pd.DataFrame):
    return pd_is_not_null(df) and "filter_result" in df.columns


def is_score_result_df(df: pd.DataFrame):
    return pd_is_not_null(df) and "score_result" in df.columns


def pd_is_not_null(df: Union[pd.DataFrame, pd.Series]):
    return df is not None and not df.empty


def group_by_entity_id(input_df: pd.DataFrame):
    return input_df.groupby(level=0)


def normalize_group_compute_result(group_result):
    if group_result.index.nlevels == 3:
        return group_result.reset_index(level=0, drop=True)
    return group_result


def merge_filter_result(input_df: pd.DataFrame, filter_result: pd.Series):
    if is_filter_result_df(input_df):
        input_df["filter_result"] = input_df["filter_result"] & filter_result
    else:
        input_df["filter_result"] = filter_result

    return input_df


def index_df(df, index="timestamp", inplace=True, drop=False, time_field="timestamp"):
    if time_field:
        df[time_field] = pd.to_datetime(df[time_field])

    if inplace:
        df.set_index(index, drop=drop, inplace=inplace)
    else:
        df = df.set_index(index, drop=drop, inplace=inplace)

    if type(index) == str:
        df = df.sort_index()
    elif type(index) == list:
        df.index.names = index
        level = list(range(len(index)))
        df = df.sort_index(level=level)
    return df


def normal_index_df(df, category_field="entity_id", time_filed="timestamp", drop=True):
    index = [category_field, time_filed]
    if is_normal_df(df):
        return df

    return index_df(df=df, index=index, drop=drop, time_field="timestamp")


def is_normal_df(df, category_field="entity_id", time_filed="timestamp"):
    if pd_is_not_null(df):
        names = df.index.names

        if len(names) == 2 and names[0] == category_field and names[1] == time_filed:
            return True

    return False


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


# the __all__ is generated
__all__ = [
    "pd_is_not_null",
    "index_df",
    "normal_index_df",
    "is_normal_df",
    "df_subset",
    "fill_with_same_index",
    "drop_continue_duplicate",
]
