# -*- coding: utf-8 -*-
import datetime
from typing import List, Union

import numpy as np
import pandas as pd

from zvt.api import get_kdata, AdjustType
from zvt.contract import IntervalLevel, EntityMixin
from zvt.domain import Stock
from zvt.factors import TargetSelector, Accumulator
from zvt.factors.ma.ma_factor import ImprovedMaFactor
from zvt.factors.top_bottom_factor import TopBottomFactor
from zvt.trader.trader import StockTrader
from zvt.utils.pd_utils import pd_is_not_null


class CrossTopBottomFactor(TopBottomFactor):
    def __init__(self, entity_schema: EntityMixin = Stock, provider: str = None, entity_provider: str = None,
                 entity_ids: List[str] = None, exchanges: List[str] = None, codes: List[str] = None,
                 the_timestamp: Union[str, pd.Timestamp] = None, start_timestamp: Union[str, pd.Timestamp] = None,
                 end_timestamp: Union[str, pd.Timestamp] = None,
                 columns: List = ['id', 'entity_id', 'timestamp', 'level', 'open', 'close', 'high', 'low'],
                 filters: List = None, order: object = None, limit: int = None,
                 level: Union[str, IntervalLevel] = IntervalLevel.LEVEL_1DAY, category_field: str = 'entity_id',
                 time_field: str = 'timestamp', computing_window: int = None, keep_all_timestamp: bool = False,
                 fill_method: str = 'ffill', effective_number: int = None, accumulator: Accumulator = None,
                 need_persist: bool = False, dry_run: bool = False, adjust_type: Union[AdjustType, str] = None,
                 window=40) -> None:
        super().__init__(entity_schema, provider, entity_provider, entity_ids, exchanges, codes, the_timestamp,
                         start_timestamp, end_timestamp, columns, filters, order, limit, level, category_field,
                         time_field, computing_window, keep_all_timestamp, fill_method, effective_number, accumulator,
                         need_persist, dry_run, adjust_type, window)

    def do_compute(self):
        super().do_compute()
        s = (self.factor_df['close'] >= 0.85 * self.factor_df['top']) & (
                self.factor_df['close'] <= 1.3 * self.factor_df['bottom'])
        self.result_df = s.to_frame(name='score')


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
        # 底部附近突破
        cross_factor = CrossTopBottomFactor(entity_ids=entity_ids, entity_schema=entity_schema, exchanges=exchanges,
                                            codes=codes, start_timestamp=start_timestamp - datetime.timedelta(365),
                                            end_timestamp=end_timestamp,
                                            provider='joinquant', level=IntervalLevel.LEVEL_1DAY)
        ma_vol_selector.add_filter_factor(ma_vol_factor)
        ma_vol_selector.add_filter_factor(cross_factor)

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
        if positions:
            entity_ids = [position.entity_id for position in positions]
            # 有效跌破5日线，卖出
            input_df = get_kdata(entity_ids=entity_ids, start_timestamp=timestamp - datetime.timedelta(20),
                                 end_timestamp=timestamp, columns=['entity_id', 'close'],
                                 index=['entity_id', 'timestamp'])
            ma_df = input_df['close'].groupby(level=0).rolling(window=10, min_periods=10).mean()
            ma_df = ma_df.reset_index(level=0, drop=True)
            input_df['ma10'] = ma_df
            s = input_df['close'] < input_df['ma10']
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
    trader = MaVolTrader(start_timestamp='2020-01-01', end_timestamp='2020-07-10')
    trader.run()
