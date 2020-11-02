# -*- coding: utf-8 -*-
import datetime
from typing import List

import numpy as np

from zvt import init_log
from zvt.api import get_kdata
from zvt.contract import IntervalLevel
from zvt.contract.api import get_entities
from zvt.domain import Stock
from zvt.factors import TargetSelector, ImprovedMaFactor
from zvt.informer.informer import EmailInformer
from zvt.trader import TradingSignal, TradingSignalType
from zvt.trader.trader import StockTrader
from zvt.utils.pd_utils import pd_is_not_null
from zvt.utils.time_utils import now_pd_timestamp


def entity_ids_to_msg(entity_ids):
    if entity_ids:
        stocks = get_entities(provider='joinquant', entity_schema=Stock, entity_ids=entity_ids,
                              return_type='domain')

        info = [f'{stock.name}({stock.code})' for stock in stocks]
        return ' '.join(info)
    return ''


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

            entity_ids = []
            for entity_id in long_targets:
                # 获取最近3k线
                df = get_kdata(entity_id=entity_id, start_timestamp=timestamp - datetime.timedelta(20),
                               end_timestamp=timestamp, columns=['entity_id', 'close', 'open', 'high', 'low'])
                if pd_is_not_null(df) and len(df) >= 3:
                    df = df.iloc[-3:]
                    # 收阳
                    se = df['close'] > df['open']
                    positive = np.all(se)
                    # 高点比高点高
                    trending = df['high'][0] < df['high'][1] < df['high'][2]

                    if positive and trending:
                        entity_ids.append(entity_id)

            return entity_ids
        return long_targets

    def select_short_targets_from_levels(self, timestamp):
        positions = self.get_current_positions()
        if positions:
            entity_ids = [position.entity_id for position in positions]
            # 有效跌破10日线，卖出
            input_df = get_kdata(entity_ids=entity_ids, start_timestamp=timestamp - datetime.timedelta(20),
                                 end_timestamp=timestamp, columns=['entity_id', 'close'],
                                 index=['entity_id', 'timestamp'])
            ma_df = input_df['close'].groupby(level=0).rolling(window=10, min_periods=10).mean()
            ma_df = ma_df.reset_index(level=0, drop=True)
            input_df['ma10'] = ma_df
            s = input_df['close'] < input_df['ma10']
            input_df = s.to_frame(name='score')

            # 连续3日收在10日线下
            df = input_df['score'].groupby(level=0).rolling(window=3, min_periods=3).apply(
                lambda x: np.logical_and.reduce(x))
            df = df.reset_index(level=0, drop=True)
            input_df['score'] = df

            result_df = input_df[input_df['score'] == 1.0]
            if pd_is_not_null(result_df):
                short_df = result_df.loc[(slice(None), slice(timestamp, timestamp)), :]
                if pd_is_not_null(short_df):
                    return short_df.index.get_level_values(0).tolist()

    def long_position_control(self):
        return 1.0

    def on_trading_signals(self, trading_signals: List[TradingSignal]):
        # 发送交易信号
        target_date = trading_signals[0].happen_timestamp

        # 发送最近20天的交易信号
        if target_date + datetime.timedelta(20) > now_pd_timestamp():
            email_action = EmailInformer()

            msg = ''

            # 目前持仓情况
            positions = self.get_current_positions()
            if positions:
                current_stocks = [position.entity_id for position in positions]
                msg = msg + '目前持仓: ' + entity_ids_to_msg(current_stocks) + '\n'

            # 多空信号
            long_stocks = []
            short_stocks = []

            for trading_signal in trading_signals:
                if trading_signal.trading_signal_type == TradingSignalType.open_long:
                    long_stocks.append(trading_signal.entity_id)
                elif trading_signal.trading_signal_type == TradingSignalType.close_long:
                    short_stocks.append(trading_signal.entity_id)

            if long_stocks:
                msg = msg + '买入: ' + entity_ids_to_msg(long_stocks) + '\n'

            if short_stocks:
                msg = msg + '卖出: ' + entity_ids_to_msg(short_stocks) + '\n'

            # 账户情况
            account = self.get_current_account()

            pct = round((account.all_value - account.input_money) / account.input_money * 100, 4)

            msg = msg + f'投入金额:{account.input_money},目前总市值:{account.all_value},收益率:{pct}%'

            email_action.send_message("5533061@qq.com", f'{target_date} 交易信号', msg)

        super().on_trading_signals(trading_signals)


if __name__ == '__main__':
    init_log('ma250_trader.log')

    trader = MaVolTrader(start_timestamp='2020-01-01', end_timestamp='2021-01-01')
    trader.run()
