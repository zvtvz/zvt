# -*- coding: utf-8 -*-
import logging
import queue
from typing import List

import pandas as pd

from zvt.domain import SecurityType
from zvt.selector.selector import TargetSelector
from zvt.trader import TradingSignal, TradingSignalType
from zvt.trader.account import SimAccountService
from zvt.utils.time_utils import to_pd_timestamp, now_pd_timestamp


class Trader(object):
    logger = logging.getLogger(__name__)

    def __init__(self, security_type=SecurityType.stock, exchanges=['sh', 'sz'], codes=None,
                 start_timestamp=None,
                 end_timestamp=None) -> None:

        self.trader_name = type(self).__name__.lower()
        self.trading_signal_queue = queue.Queue()
        self.trading_signal_listeners = []
        self.state_listeners = []

        self.selectors: List[TargetSelector] = None

        self.security_type = security_type
        self.exchanges = exchanges
        self.codes = codes
        self.start_timestamp = start_timestamp
        self.end_timestamp = end_timestamp

        if self.start_timestamp:
            self.start_timestamp = to_pd_timestamp(self.start_timestamp)
        else:
            self.start_timestamp = now_pd_timestamp()

        self.current_timestamp = self.start_timestamp

        if self.end_timestamp:
            self.end_timestamp = to_pd_timestamp(self.end_timestamp)

        self.account_service = SimAccountService(trader_name=self.trader_name,
                                                 timestamp=self.start_timestamp)

        self.add_trading_signal_listener(self.account_service)

        self.init_selectors(security_type=self.security_type, exchanges=self.exchanges, codes=self.codes,
                            start_timestamp=self.start_timestamp, end_timestamp=self.end_timestamp)

    def init_selectors(self, security_type, exchanges, codes, start_timestamp, end_timestamp):
        """
        implement this to init selectors

        :param security_type:
        :type security_type:
        :param exchanges:
        :type exchanges:
        :param codes:
        :type codes:
        :param start_timestamp:
        :type start_timestamp:
        :param end_timestamp:
        :type end_timestamp:
        """
        raise NotImplementedError

    def send_trading_signal(self, trading_signal):
        self.trading_signal_queue.put(trading_signal)

    def add_trading_signal_listener(self, listener):
        if listener not in self.trading_signal_listeners:
            self.trading_signal_listeners.append(listener)

    def remove_trading_signal_listener(self, listener):
        if listener in self.trading_signal_listeners:
            self.trading_signal_listeners.remove(listener)

    def run(self):
        # now we just support day level
        for timestamp in pd.date_range(start=self.start_timestamp, end=self.end_timestamp,
                                       freq='B').tolist():

            account = self.account_service.get_account_at_time(timestamp)
            positions = [position.security_id for position in account.positions]

            # select the targets from the selectors
            selected = set()
            for selector in self.selectors:
                df = selector.get_targets(timestamp)
                if not df.empty:
                    targets = set(df['security_id'].to_list())
                    if not selected:
                        selected = targets
                    else:
                        selected = selected & targets

            if selected:
                # just long the security not in the positions
                longed = selected - set(positions)
                position_pct = 1.0 / len(longed)

                for security_id in longed:
                    trading_signal = TradingSignal(security_id=security_id,
                                                   the_timestamp=timestamp,
                                                   trading_signal_type=TradingSignalType.trading_signal_open_long,
                                                   trading_level=None,
                                                   position_pct=position_pct)
                    for listener in self.trading_signal_listeners:
                        listener.on_trading_signal(trading_signal)

            shorted = set(positions) - selected

            for security_id in shorted:
                trading_signal = TradingSignal(security_id=security_id,
                                               the_timestamp=timestamp,
                                               trading_signal_type=TradingSignalType.trading_signal_close_long,
                                               trading_level=None)
                for listener in self.trading_signal_listeners:
                    listener.on_trading_signal(trading_signal)

            self.account_service.save_closing_account(timestamp)
