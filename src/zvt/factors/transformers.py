# -*- coding: utf-8 -*-
import numpy as np
import pandas as pd

from zvt.contract.factor import Transformer
from zvt.factors.algorithm import MaTransformer
from zvt.factors.technical_factor import TechnicalFactor
from zvt.utils.pd_utils import group_by_entity_id, normalize_group_compute_result, merge_filter_result
from zvt.utils.time_utils import to_pd_timestamp


def _cal_state(s, df, pre, interval, col):
    assert len(s) == pre + interval
    s = df.loc[s.index, :]
    pre_df: pd.DataFrame = s.iloc[:pre, :]
    recent_df: pd.DataFrame = s.iloc[-interval:, :]
    if pre_df.isnull().values.any() or recent_df.isnull().values.any():
        return np.nan
    pre_result = np.logical_and.reduce(pre_df["close"] > pre_df[col])
    recent_result = np.logical_and.reduce(recent_df["close"] < recent_df[col])
    if pre_result and recent_result:
        return True
    return np.nan


class CrossMaTransformer(MaTransformer):
    def __init__(self, windows=None, cal_change_pct=False) -> None:
        super().__init__(windows, cal_change_pct)

    def transform(self, input_df: pd.DataFrame) -> pd.DataFrame:
        input_df = super().transform(input_df)
        cols = [f"ma{window}" for window in self.windows]
        s = input_df[cols[0]] > input_df[cols[1]]
        current_col = cols[1]
        for col in cols[2:]:
            s = s & (input_df[current_col] > input_df[col])
            current_col = col
        input_df["filter_result"] = s
        return input_df


class SpecificTransformer(Transformer):
    def __init__(self, buy_timestamp, sell_timestamp) -> None:
        self.buy_timestamp = to_pd_timestamp(buy_timestamp)
        self.sell_timestamp = to_pd_timestamp(sell_timestamp)

    def transform(self, input_df: pd.DataFrame) -> pd.DataFrame:
        s = input_df[input_df.get_level_values["timestamp"] == self.buy_timestamp]
        s[s == False] = None
        s[input_df.get_level_values["timestamp"] == self.sell_timestamp] = False
        input_df["filter_result"] = s
        return input_df


class FallBelowTransformer(Transformer):
    def __init__(self, window=10, interval=3) -> None:
        super().__init__()
        self.window = window
        self.interval = interval

    def transform(self, input_df: pd.DataFrame) -> pd.DataFrame:
        col = f"ma{self.window}"
        if col not in input_df.columns:
            group_result = (
                group_by_entity_id(input_df["close"]).rolling(window=self.window, min_periods=self.window).mean()
            )
            group_result = normalize_group_compute_result(group_result=group_result)
            input_df[col] = group_result

        # 连续3(interval)日收在10(window)日线下
        s = input_df["close"] < input_df[col]
        s = (
            group_by_entity_id(s)
            .rolling(window=self.interval, min_periods=self.interval)
            .apply(lambda x: np.logical_and.reduce(x))
        )
        s = normalize_group_compute_result(group_result=s)
        # 构造卖点
        s[s == False] = None
        s[s == True] = False
        input_df = merge_filter_result(input_df=input_df, filter_result=s)

        return input_df


if __name__ == "__main__":
    # df = Stock1dHfqKdata.query_data(codes=["000338"], index=["entity_id", "timestamp"])
    # df = FallBelowTransformer().transform(df)
    # print(df["filter_result"])
    TechnicalFactor(transformer=SpecificTransformer(timestamp="2020-03-01"))


# the __all__ is generated
__all__ = ["CrossMaTransformer", "SpecificTransformer", "FallBelowTransformer"]
