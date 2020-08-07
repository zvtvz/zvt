# -*- coding: utf-8 -*-
import datetime

import numpy as np

from zvt.api import get_kdata
from zvt.contract import IntervalLevel
from zvt.factors import TargetSelector
from zvt.factors import TechnicalFactor
from zvt.factors.ma.ma_factor import CrossMaFactor
from zvt.trader.trader import StockTrader
from zvt.utils.pd_utils import pd_is_not_null


class GoldBullFactor(TechnicalFactor):
    keep_window = 10

    def do_compute(self):
        super().do_compute()
        # 金叉
        self.factor_df['cross'] = self.factor_df['diff'] > self.factor_df['dea']
        # 黄白线在0轴上
        self.factor_df['bull'] = (self.factor_df['diff'] > 0) & (self.factor_df['dea'] > 0)
        # 黄白线在0轴上持续了10天以上
        df = self.factor_df['bull'].groupby(level=0).rolling(window=self.keep_window,
                                                             min_periods=self.keep_window).apply(
            lambda x: np.logical_and.reduce(x))
        df = df.reset_index(level=0, drop=True)

        s = self.factor_df['cross'] & df
        self.result_df = s.to_frame(name='score')


class VolMacdTrader(StockTrader):
    def init_selectors(self, entity_ids, entity_schema, exchanges, codes, start_timestamp, end_timestamp):
        # 周线策略
        week_selector = TargetSelector(entity_ids=entity_ids, entity_schema=entity_schema, exchanges=exchanges,
                                       codes=codes, start_timestamp=start_timestamp, end_timestamp=end_timestamp,
                                       provider='joinquant', level=IntervalLevel.LEVEL_1WEEK)
        week_bull_factor = GoldBullFactor(entity_ids=entity_ids, entity_schema=entity_schema, exchanges=exchanges,
                                          codes=codes, start_timestamp=start_timestamp, end_timestamp=end_timestamp,
                                          provider='joinquant', level=IntervalLevel.LEVEL_1WEEK)
        week_selector.add_filter_factor(week_bull_factor)

        # 日线策略
        day_selector = TargetSelector(entity_ids=entity_ids, entity_schema=entity_schema, exchanges=exchanges,
                                      codes=codes, start_timestamp=start_timestamp, end_timestamp=end_timestamp,
                                      provider='joinquant', level=IntervalLevel.LEVEL_1DAY)
        cross_ma_factor = CrossMaFactor(entity_ids=entity_ids, entity_schema=entity_schema, exchanges=exchanges,
                                        codes=codes, start_timestamp=start_timestamp, end_timestamp=end_timestamp,
                                        provider='joinquant', level=IntervalLevel.LEVEL_1DAY, windows=[5, 250])

        day_selector.add_filter_factor(cross_ma_factor)

        self.selectors.append(week_selector)
        self.selectors.append(day_selector)

    def select_long_targets_from_levels(self, timestamp):
        # self.level_map_long_targets里面是各级别选中的标的，默认是各级别都选中才要
        long_targets = super().select_long_targets_from_levels(timestamp)

        if self.level >= IntervalLevel.LEVEL_1DAY:
            if not long_targets:
                return None

            df = get_kdata(entity_ids=list(long_targets), start_timestamp=timestamp, end_timestamp=timestamp,
                           columns=['entity_id', 'turnover'])
            if pd_is_not_null(df):
                df.sort_values(by=['turnover'])
                if len(df['entity_id']) > 5:
                    return df['entity_id'].iloc[5:10].tolist()
                return df['entity_id'].tolist()
            return None
        return long_targets

    def select_short_targets_from_levels(self, timestamp):
        # 因为不能做空，只从持仓里面算出需要卖的个股
        positions = self.get_current_positions()
        if positions:
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
    trader = VolMacdTrader(start_timestamp='2017-01-01', end_timestamp='2020-01-01')
    trader.run()
    # f = VolFactor(start_timestamp='2020-01-01', end_timestamp='2020-04-01')
    # print(f.result_df)
