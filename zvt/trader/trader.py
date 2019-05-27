# -*- coding: utf-8 -*-
import logging
from typing import List

import pandas as pd

from zvt.api.rules import iterate_timestamps, is_open_time, is_in_finished_timestamps, is_close_time
from zvt.charts.business import draw_account_details, draw_order_signals
from zvt.domain import SecurityType, TradingLevel, Provider
from zvt.selectors.selector import TargetSelector
from zvt.trader import TradingSignal, TradingSignalType
from zvt.trader.account import SimAccountService
from zvt.utils.time_utils import to_pd_timestamp

logger = logging.getLogger(__name__)


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

    def make_decision(self, timestamp, trading_level):
        df_result = pd.DataFrame()
        for selector in self.selectors:
            if selector.level == trading_level:
                df = selector.get_targets(timestamp)
                if not df.empty:
                    df = df.sort_values(by=['security_id', 'score'])
                    if len(df.index) > self.limit:
                        df = df.iloc[list(range(self.limit)), :]
                df_result = df_result.append(df)
        return df_result


class TargetsSlot(object):

    def __init__(self) -> None:
        self.level_map_targets = {}

    def input_targets(self, level: TradingLevel, targets: List[str]):
        logger.info('level:{},old targets:{},new targets:{}'.format(level,
                                                                    self.get_targets(level), targets))
        self.level_map_targets[level.value] = targets

    def get_targets(self, level: TradingLevel):
        return self.level_map_targets.get(level.value)


class Trader(object):
    logger = logging.getLogger(__name__)

    # overwrite it to custom your trader
    selectors_comparator = SelectorsComparator(limit=10)

    def __init__(self, security_type=SecurityType.stock, exchanges=['sh', 'sz'], codes=None,
                 start_timestamp=None,
                 end_timestamp=None,
                 provider=Provider.JOINQUANT,
                 trading_level=TradingLevel.LEVEL_1DAY,
                 trader_name=None) -> None:
        if trader_name:
            self.trader_name = trader_name
        else:
            self.trader_name = type(self).__name__.lower()
        self.trading_signal_listeners = []
        self.state_listeners = []

        self.selectors: List[TargetSelector] = None

        self.security_type = security_type
        self.exchanges = exchanges
        self.codes = codes
        # make sure the min level selector correspond to the provider and level
        self.provider = provider
        self.trading_level = trading_level

        if start_timestamp and end_timestamp:
            self.start_timestamp = to_pd_timestamp(start_timestamp)
            self.end_timestamp = to_pd_timestamp(end_timestamp)
        else:
            assert False

        self.account_service = SimAccountService(trader_name=self.trader_name,
                                                 timestamp=self.start_timestamp,
                                                 provider=self.provider,
                                                 level=self.trading_level)

        self.add_trading_signal_listener(self.account_service)

        self.init_selectors(security_type=self.security_type, exchanges=self.exchanges, codes=self.codes,
                            start_timestamp=self.start_timestamp, end_timestamp=self.end_timestamp)

        self.selectors_comparator.add_selectors(self.selectors)

        self.trading_levels = list(set([TradingLevel(selector.level) for selector in self.selectors]))

        self.targets_slot: TargetsSlot = TargetsSlot()

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

    def handle_targets_slot(self, timestamp):
        # handling max level to min level
        self.trading_levels.sort(reverse=True)

        # the default behavior is select the targets in all levels
        selected = None
        for level in self.trading_levels:
            current = self.targets_slot.get_targets(level=level)
            if not current:
                current = {}

            if not selected:
                selected = current
            else:
                selected = selected & current

        if selected:
            self.logger.info('timestamp:{},selected:{}'.format(timestamp, selected))

        self.send_trading_signals(timestamp=timestamp, selected=selected)

    def send_trading_signals(self, timestamp, selected):
        # current position
        account = self.account_service.latest_account
        current_holdings = [position['security_id'] for position in account['positions']]

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
                                                   trading_level=self.trading_level,
                                                   order_money=order_money)
                    for listener in self.trading_signal_listeners:
                        listener.on_trading_signal(trading_signal)

        # just short the security not in the selected but in current_holdings
        if selected:
            shorted = set(current_holdings) - selected
        else:
            shorted = set(current_holdings)

        for security_id in shorted:
            trading_signal = TradingSignal(security_id=security_id,
                                           the_timestamp=timestamp,
                                           trading_signal_type=TradingSignalType.trading_signal_close_long,
                                           position_pct=1.0,
                                           trading_level=self.trading_level)
            for listener in self.trading_signal_listeners:
                listener.on_trading_signal(trading_signal)

    def on_finish(self):
        draw_account_details(trader_name=self.trader_name)
        draw_order_signals(trader_name=self.trader_name)

    def run(self):
        # iterate timestamp of the min level
        for timestamp in iterate_timestamps(security_type=self.security_type, exchange=self.exchanges[0],
                                            start_timestamp=self.start_timestamp, end_timestamp=self.end_timestamp,
                                            level=self.trading_level):
            # on_trading_open to setup the account
            if self.trading_level == TradingLevel.LEVEL_1DAY or (
                    self.trading_level != TradingLevel.LEVEL_1DAY and is_open_time(security_type=self.security_type,
                                                                                   exchange=self.exchanges[0],
                                                                                   timestamp=timestamp)):
                self.account_service.on_trading_open(timestamp)

            # handle trading_signal_slo
            self.handle_targets_slot(timestamp=timestamp)

            # handle selector
            for level in self.trading_levels:
                if (is_in_finished_timestamps(security_type=self.security_type, exchange=self.exchanges[0],
                                              timestamp=timestamp, level=level)):
                    df = self.selectors_comparator.make_decision(timestamp=timestamp,
                                                                 trading_level=level)
                    if not df.empty:
                        selected = set(df['security_id'].to_list())
                    else:
                        selected = {}

                    self.targets_slot.input_targets(level, selected)

            # on_trading_close to calculate date account
            if self.trading_level == TradingLevel.LEVEL_1DAY or (
                    self.trading_level != TradingLevel.LEVEL_1DAY and is_close_time(security_type=self.security_type,
                                                                                    exchange=self.exchanges[0],
                                                                                    timestamp=timestamp)):
                self.account_service.on_trading_close(timestamp)

        self.on_finish()
