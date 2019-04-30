# -*- coding: utf-8 -*-
import enum
import queue

import pandas as pd

from zvt.api.common import get_close_time
from zvt.trader.account import SimAccountService
from zvt.utils.pd_utils import index_df_with_time
from zvt.utils.time_utils import to_pd_timestamp


class ModelType(enum.Enum):
    TECHNICAL_MODEL = 'technical_model'
    FUNDAMENTAL_MODEL = 'fundamental_model'
    NEWS_MODEL = 'news_model'


class Model(object):
    history_data = None
    current_timestamp = None
    current_data = None
    security_id = None
    trading_level = None
    model_type = None
    state = None
    close_hour = None
    close_minute = None
    account_service = None
    model_name = None

    trading_signal_queue = queue.Queue()

    trading_signal_listeners = []
    state_listeners = []

    def __init__(self, security_id, trading_level, timestamp, trader_name, history_size=250) -> None:
        self.security_id = security_id
        self.trading_level = trading_level
        self.current_timestamp = trading_level.floor_timestamp(to_pd_timestamp(timestamp))

        self.model_name = "{}_{}_{}".format(trader_name, type(self).__name__, trading_level.value)

        self.history_size = history_size

        self.add_trading_signal_listener(SimAccountService(trader_name=trader_name, model_name=self.model_name,
                                                           timestamp=timestamp))

        self.close_hour, self.close_minute = get_close_time(self.security_id)

    def init_history_data(self, history_data):
        self.history_data = pd.DataFrame(history_data)
        self.history_data = index_df_with_time(self.history_data)
        self.current_timestamp = to_pd_timestamp(history_data[-1]['timestamp'])
        self.current_data = history_data[-1]

    def send_trading_signal(self, trading_signal):
        self.trading_signal_queue.put(trading_signal)

    def append_data(self, data):
        if self.history_data is None:
            self.history_data = pd.DataFrame()

        # TODO:open this check latter
        # delta = to_pd_timestamp(data['timestamp']) - to_pd_timestamp(self.current_data['timestamp'])
        # if delta.total_seconds() != self.trading_level.to_second():
        #     raise WrongOrderKdataError()

        self.history_data = self.history_data.append(data)
        self.current_timestamp = data.name
        self.current_data = data

        self.make_decision()

        while True:
            if self.trading_signal_queue.empty():
                break
            trading_signal = self.trading_signal_queue.get(block=False)
            if trading_signal is None:
                break

            for l in self.trading_signal_listeners:
                l.on_trading_signal(trading_signal)

        for l in self.state_listeners:
            l.on_state_change(self.state)

        if self.trading_level.is_last_data_of_day(self.close_hour, self.close_minute, self.current_timestamp):
            self.account_service.calculate_closing_account(self.current_timestamp)

    def evaluate_fetch_interval(self, end_timestamp):
        if not self.current_timestamp:
            self.current_timestamp = end_timestamp
            return None, None
        time_delta = end_timestamp - self.current_timestamp
        if time_delta.total_seconds() >= self.trading_level.to_second():
            return self.current_timestamp + pd.Timedelta(seconds=self.trading_level.to_second()), end_timestamp
        return None, None

    def get_state(self):
        return self.state

    def make_decision(self):
        pass

    def add_trading_signal_listener(self, l):
        if l not in self.trading_signal_listeners:
            self.trading_signal_listeners.append(l)

    def remove_trading_signal_listener(self, l):
        if l in self.trading_signal_listeners:
            self.trading_signal_listeners.remove(l)

    def add_state_listener(self, l):
        if l not in self.state_listeners:
            self.state_listeners.append(l)

    def remove_state_listener(self, l):
        if l in self.state_listeners:
            self.state_listeners.remove(l)

    def signal_timestamp_interval(self):
        return self.current_timestamp, self.current_timestamp + pd.Timedelta(seconds=self.trading_level.to_second())
