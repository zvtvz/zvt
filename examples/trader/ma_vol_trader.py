# -*- coding: utf-8 -*-
import datetime
from typing import List

import numpy as np

from zvt.api import get_kdata
from zvt.contract import IntervalLevel
from zvt.factors import TargetSelector
from zvt.factors.ma.ma_factor import ImprovedMaFactor
from zvt.trader.trader import StockTrader
from zvt.utils.pd_utils import pd_is_not_null


class MaVolTrader(StockTrader):
    def init_selectors(self, entity_ids, entity_schema, exchanges, codes, start_timestamp, end_timestamp):
        ma_vol_selector = TargetSelector(entity_ids=entity_ids, entity_schema=entity_schema, exchanges=exchanges,
                                         codes=codes, start_timestamp=start_timestamp, end_timestamp=end_timestamp,
                                         provider='joinquant', level=IntervalLevel.LEVEL_1DAY)
        # 放量突破年线
        ma_vol_factor = ImprovedMaFactor(entity_ids=entity_ids, entity_schema=entity_schema, exchanges=exchanges,
                                         codes=codes, start_timestamp=start_timestamp - datetime.timedelta(365),
                                         end_timestamp=end_timestamp,
                                         provider='joinquant', level=IntervalLevel.LEVEL_1DAY)
        ma_vol_selector.add_filter_factor(ma_vol_factor)

        self.selectors.append(ma_vol_selector)

    def filter_selector_long_targets(self, timestamp, selector: TargetSelector, long_targets: List[str]) -> List[str]:
        # 选择器选出的个股，再做进一步处理
        if selector.level == IntervalLevel.LEVEL_1DAY:
            if not long_targets:
                return None

            df = get_kdata(entity_ids=long_targets, start_timestamp=timestamp, end_timestamp=timestamp,
                           columns=['entity_id', 'turnover'])
            if pd_is_not_null(df):
                df.sort_values(by=['turnover'])
                return df['entity_id'].iloc[:10].tolist()
            return None
        return long_targets

    def select_short_targets_from_levels(self, timestamp):
        positions = self.get_current_positions()
        if (positions):
            entity_ids = [position.entity_id for position in positions]
            # 有效跌破5日线，卖出
            input_df = get_kdata(entity_ids=entity_ids, start_timestamp=timestamp - datetime.timedelta(20),
                                 end_timestamp=timestamp, columns=['entity_id', 'close'],
                                 index=['entity_id', 'timestamp'])
            ma_df = input_df['close'].groupby(level=0).rolling(window=5, min_periods=5).mean()
            ma_df = ma_df.reset_index(level=0, drop=True)
            input_df['ma5'] = ma_df
            s = input_df['close'] < input_df['ma5']
            input_df = s.to_frame(name='score')

            # 连续3日收在5日线下
            df = input_df['score'].groupby(level=0).rolling(window=3, min_periods=3).apply(
                lambda x: np.logical_and.reduce(x))
            df = df.reset_index(level=0, drop=True)
            input_df['score'] = df

            result_df = input_df[input_df['score'] == 1.0]
            if pd_is_not_null(result_df):
                short_df = result_df.loc[(slice(None), slice(timestamp, timestamp)), :]
                if pd_is_not_null(short_df):
                    return short_df.index.get_level_values(0).tolist()


if __name__ == '__main__':
    trader = MaVolTrader(start_timestamp='2019-01-01', end_timestamp='2020-01-01')
    trader.run()
