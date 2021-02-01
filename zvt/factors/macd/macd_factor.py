# -*- coding: utf-8 -*-
from typing import List, Optional

import numpy as np
import pandas as pd

from zvt.factors.algorithm import MacdTransformer
from zvt.factors.technical_factor import TechnicalFactor


class MacdFactor(TechnicalFactor):
    transformer = MacdTransformer(count_live_dead=True)

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
        self.result_df = self.factor_df['bull'].to_frame(name='score')


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
        self.factor_df['pre'] = self.factor_df['live_count'].shift()
        s = (self.factor_df['pre'] <= self.pattern[0]) & (self.factor_df['live_count'] >= self.pattern[1])
        self.result_df = s.to_frame(name='score')


class GoldCrossFactor(MacdFactor):
    def compute_result(self):
        super().compute_result()
        s = self.factor_df['live'] == 1
        self.result_df = s.to_frame(name='score')


# the __all__ is generated
__all__ = ['MacdFactor', 'BullFactor', 'KeepBullFactor', 'LiveOrDeadFactor', 'GoldCrossFactor']

if __name__ == '__main__':
    from zvt.contract import IntervalLevel

    f1 = LiveOrDeadFactor(level=IntervalLevel.LEVEL_1WEEK, start_timestamp='2018-01-01')

    df = f1.factor_df
    print(df[(df['score'] > 0) & (df['timestamp'] == '2021-01-04')])
