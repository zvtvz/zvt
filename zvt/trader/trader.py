# -*- coding: utf-8 -*-
import logging
import time

import pandas as pd

from zvt.api.common import decode_security_id
from zvt.api.technical import get_kdata
from zvt.domain import TradingLevel
from zvt.api.common import get_kdata_schema
from zvt.models.technical_model import CrossMaModel
from zvt.utils.time_utils import to_pd_timestamp, now_pd_timestamp


class Trader(object):
    # backtest start time,would be now if not set
    start_timestamp = None
    # backtest end time,would not stop if not net
    end_timestamp = None

    current_timestamp = None
    # the trading level of the trader
    trading_level = None
    # trading_level of model must <= self.trading_level
    models = []
    security_id = None

    missing_data = False

    logger = logging.getLogger(__name__)

    def __init__(self) -> None:
        if self.start_timestamp:
            self.start_timestamp = to_pd_timestamp(self.start_timestamp)
            self.start_timestamp = self.trading_level.floor_timestamp(self.start_timestamp)
            self.current_timestamp = self.start_timestamp
        else:
            self.start_timestamp = now_pd_timestamp()

        if self.end_timestamp:
            self.end_timestamp = to_pd_timestamp(self.end_timestamp)

        self.security_type, self.exchange, self.code = decode_security_id(self.security_id)

        self.kdata_schema = get_kdata_schema(self.security_type)

        # init history data
        for model in self.models:
            datas = \
                get_kdata(self.security_id, level=model.trading_level,
                          end_timestamp=self.start_timestamp, order=self.kdata_schema.timestamp.desc(),
                          limit=model.history_size)
            if datas:
                model.init_history_data(datas)

            if not datas:
                self.logger.warning(
                    "to {}, {} no history data ".format(self.start_timestamp, self.security_id))
            elif len(datas) < self.history_data_size:
                self.logger.warning(
                    "to {}, {} history data size:{}".format(self.start_timestamp, self.security_id, len(datas)))

    def on_next_period(self):
        for model in self.models:
            start_timestamp, end_timestamp = model.evaluate_fetch_interval(self.current_timestamp)
            if start_timestamp and end_timestamp:
                retry_times = 10
                while retry_times > 0:
                    datas = get_kdata(self.security_id, level=model.trading_level.value,
                                      start_timestamp=start_timestamp, end_timestamp=end_timestamp)
                    if not datas:
                        self.logger.warning(
                            "no kdata for security:{},trading_level:{},start_timestamp:{} end_timestamp:{} ".format(
                                self.security_id, model.trading_level, start_timestamp, end_timestamp))
                        retry_times = retry_times - 1
                        continue
                    for data in datas:
                        series_data = pd.Series(data)
                        series_data.name = to_pd_timestamp(data['timestamp'])
                        model.append_data(series_data)
                    break

    def run(self):
        while True:
            if self.end_timestamp and self.current_timestamp >= self.end_timestamp:
                return

            self.on_next_period()

            # time just add for backtest
            self.current_timestamp += pd.Timedelta(seconds=self.trading_level.to_second())

            if self.current_timestamp > now_pd_timestamp():
                delta = self.current_timestamp - now_pd_timestamp()
                time.sleep(delta.total_seconds())


class TestTrader(Trader):
    security_id = 'coin_binance_EOS-USDT'
    start_timestamp = '2018-06-28'
    trading_level = TradingLevel.LEVEL_1DAY

    models = [CrossMaModel(security_id=security_id, trading_level=trading_level, trader_name='test_trader',
                           timestamp=start_timestamp)]

    def on_next_period(self):
        super().on_next_period()
        # check the models decision
        # check the models state


if __name__ == '__main__':
    test_trader = TestTrader()
    test_trader.run()
