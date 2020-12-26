# -*- coding: utf-8 -*-
from typing import List, Optional

import numpy as np
import pandas as pd

from zvt.factors.algorithm import MacdTransformer, consecutive_count
from zvt.factors.technical_factor import TechnicalFactor


class MacdFactor(TechnicalFactor):
    transformer = MacdTransformer()

    def drawer_factor_df_list(self) -> Optional[List[pd.DataFrame]]:
        return None

    def drawer_sub_df_list(self) -> Optional[List[pd.DataFrame]]:
        return [self.factor_df[['diff', 'dea', 'macd']]]

    def drawer_sub_col_chart(self) -> Optional[dict]:
        return {'diff': 'line',
                'dea': 'line',
                'macd': 'bar'}


class BullFactor(MacdFactor):
    def compute_result(self):
        super().compute_result()
        # 黄白线在0轴上
        s = (self.factor_df['diff'] > 0) & (self.factor_df['dea'] > 0)
        self.result_df = s.to_frame(name='score')


class KeepBullFactor(BullFactor):
    keep_window = 20

    def compute_result(self):
        super().compute_result()
        df = self.result_df['score'].groupby(level=0).rolling(window=self.keep_window,
                                                              min_periods=self.keep_window).apply(
            lambda x: np.logical_and.reduce(x))
        df = df.reset_index(level=0, drop=True)
        self.result_df['score'] = df


# 金叉 死叉 持续时间 切换点
class LiveOrDeadFactor(MacdFactor):
    pattern = [-5, 1]

    def compute_result(self):
        super().compute_result()
        # 白线在黄线之上
        s = self.factor_df['diff'] > self.factor_df['dea']
        # live=True 白线>黄线
        # live=False 白线<黄线
        self.factor_df['live'] = s.to_frame()
        consecutive_count(self.factor_df, 'live', pattern=self.pattern)
        self.result_df = self.factor_df[['score']]


class GoldCrossFactor(MacdFactor):
    def compute_result(self):
        super().compute_result()
        # 白线在黄线之上
        s = self.factor_df['diff'] > self.factor_df['dea']
        # live=True 白线>黄线
        # live=False 白线<黄线
        self.factor_df['live'] = s.to_frame()
        s = self.factor_df['live'] == 1
        self.result_df = s.to_frame(name='score')


# the __all__ is generated
__all__ = ['MacdFactor', 'BullFactor', 'KeepBullFactor', 'LiveOrDeadFactor', 'GoldCrossFactor']
