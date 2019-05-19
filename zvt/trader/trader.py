# -*- coding: utf-8 -*-
import logging
from typing import List

import pandas as pd

from zvt.domain import SecurityType, TradingLevel
from zvt.selectors.selector import TargetSelector
from zvt.trader import TradingSignal, TradingSignalType
from zvt.trader.account import SimAccountService
from zvt.utils.time_utils import to_pd_timestamp


class SelectorsComparator(object):

    def __init__(self, limit=10) -> None:
        self.selectors: List[TargetSelector] = []
        self.limit = limit

    def add_selector(self, selector):
        """

        :param selector:
        :type selector: TargetSelector
        """
        self.selectors.append(selector)

    def add_selectors(self, selectors):
        """

        :param selectors:
        :type selectors: List[TargetSelector]
        """
        self.selectors += selectors

    def make_decision(self, timestamp):
        df = pd.DataFrame()
        for selector in self.selectors:
            df = df.append(selector.get_targets(timestamp))
        if not df.empty:
            df = df.sort_values(by=['security_id', 'score'])
            if len(df.index) > self.limit:
                df = df.iloc[list(range(self.limit)), :]
        return df


class Trader(object):
    logger = logging.getLogger(__name__)

    # overwrite it to custom your trader
    selectors_comparator = SelectorsComparator(limit=5)

    def __init__(self, security_type=SecurityType.stock, exchanges=['sh', 'sz'], codes=None,
                 start_timestamp=None,
                 end_timestamp=None) -> None:

        self.trader_name = type(self).__name__.lower()
        self.trading_signal_listeners = []
        self.state_listeners = []

        self.selectors: List[TargetSelector] = None

        self.security_type = security_type
        self.exchanges = exchanges
        self.codes = codes

        if start_timestamp and end_timestamp:
            self.start_timestamp = to_pd_timestamp(start_timestamp)
            self.end_timestamp = to_pd_timestamp(end_timestamp)
        else:
            assert False

        self.account_service = SimAccountService(trader_name=self.trader_name,
                                                 timestamp=self.start_timestamp)

        self.add_trading_signal_listener(self.account_service)

        self.init_selectors(security_type=self.security_type, exchanges=self.exchanges, codes=self.codes,
                            start_timestamp=self.start_timestamp, end_timestamp=self.end_timestamp)

        self.selectors_comparator.add_selectors(self.selectors)

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

            self.account_service.on_trading_open(timestamp)

            account = self.account_service.latest_account
            current_holdings = [position['security_id'] for position in account['positions']]

            df = self.selectors_comparator.make_decision(timestamp=timestamp)

            selected = set()
            if not df.empty:
                selected = set(df['security_id'].to_list())

            if selected:
                # just long the security not in the positions
                longed = selected - set(current_holdings)
                if longed:
                    position_pct = 1.0 / len(longed)
                    order_money = account['cash'] * position_pct

                    for security_id in longed:
                        trading_signal = TradingSignal(security_id=security_id,
                                                       the_timestamp=timestamp,
                                                       trading_signal_type=TradingSignalType.trading_signal_open_long,
                                                       trading_level=TradingLevel.LEVEL_1DAY,
                                                       order_money=order_money)
                        for listener in self.trading_signal_listeners:
                            listener.on_trading_signal(trading_signal)

            shorted = set(current_holdings) - selected

            for security_id in shorted:
                trading_signal = TradingSignal(security_id=security_id,
                                               the_timestamp=timestamp,
                                               trading_signal_type=TradingSignalType.trading_signal_close_long,
                                               position_pct=1.0,
                                               trading_level=TradingLevel.LEVEL_1DAY)
                for listener in self.trading_signal_listeners:
                    listener.on_trading_signal(trading_signal)

            self.account_service.on_trading_close(timestamp)
