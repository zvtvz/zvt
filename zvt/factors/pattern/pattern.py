# -*- coding: utf-8 -*-
import pandas as pd

from zvt.factors import Transformer


class ZenTransformer(Transformer):
    def __init__(self) -> None:
        super().__init__()
        # 顶分型
        self.indicators.append('is_ding')
        # 顶分型力度
        self.indicators.append('ding_power')
        # 底分型
        self.indicators.append('is_di')
        # 底分型力度
        self.indicators.append('di_power')

    def transform_one(self, one_df: pd.DataFrame) -> pd.DataFrame:
        print(f'transform_one {one_df}')
