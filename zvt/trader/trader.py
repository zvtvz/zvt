# -*- coding: utf-8 -*-
import json
import logging
from typing import List, Union

import pandas as pd

from zvt.api.business_reader import AccountStatsReader
from zvt.contract import IntervalLevel, EntityMixin
from zvt.contract.api import get_db_session
from zvt.contract.normal_data import NormalData
from zvt.domain import Stock, TraderInfo, AccountStats
from zvt.drawer.drawer import Drawer
from zvt.factors.target_selector import TargetSelector
from zvt.trader import TradingSignal, TradingSignalType, TradingListener
from zvt.trader.account import SimAccountService
from zvt.utils.time_utils import to_pd_timestamp, now_pd_timestamp, to_time_str

logger = logging.getLogger(__name__)


class Trader(object):
    entity_schema: EntityMixin = None

    def __init__(self,
                 entity_ids: List[str] = None,
                 exchanges: List[str] = None,
                 codes: List[str] = None,
                 start_timestamp: Union[str, pd.Timestamp] = None,
                 end_timestamp: Union[str, pd.Timestamp] = None,
                 provider: str = None,
                 level: Union[str, IntervalLevel] = IntervalLevel.LEVEL_1DAY,
                 trader_name: str = None,
                 real_time: bool = False,
                 kdata_use_begin_time: bool = False,
                 draw_result: bool = True) -> None:
        assert self.entity_schema is not None

        self.logger = logging.getLogger(__name__)

        if trader_name:
            self.trader_name = trader_name
        else:
            self.trader_name = type(self).__name__.lower()

        self.trading_signal_listeners: List[TradingListener] = []

        self.selectors: List[TargetSelector] = []

        self.entity_ids = entity_ids

        self.exchanges = exchanges
        self.codes = codes

        self.provider = provider
        # make sure the min level selector correspond to the provider and level
        self.level = IntervalLevel(level)
        self.real_time = real_time

        if start_timestamp and end_timestamp:
            self.start_timestamp = to_pd_timestamp(start_timestamp)
            self.end_timestamp = to_pd_timestamp(end_timestamp)
        else:
            assert False

        self.trading_dates = self.entity_schema.get_trading_dates(start_date=self.start_timestamp,
                                                                  end_date=self.end_timestamp)

        if real_time:
            logger.info(
                'real_time mode, end_timestamp should be future,you could set it big enough for running forever')
            assert self.end_timestamp >= now_pd_timestamp()

        self.kdata_use_begin_time = kdata_use_begin_time
        self.draw_result = draw_result

        self.account_service = SimAccountService(entity_schema=self.entity_schema,
                                                 trader_name=self.trader_name,
                                                 timestamp=self.start_timestamp,
                                                 provider=self.provider,
                                                 level=self.level)

        self.add_trading_signal_listener(self.account_service)

        self.init_selectors(entity_ids=entity_ids, entity_schema=self.entity_schema, exchanges=self.exchanges,
                            codes=self.codes, start_timestamp=self.start_timestamp, end_timestamp=self.end_timestamp)

        if self.selectors:
            self.trading_level_asc = list(set([IntervalLevel(selector.level) for selector in self.selectors]))
            self.trading_level_asc.sort()

            self.logger.info(f'trader level:{self.level},selectors level:{self.trading_level_asc}')

            if self.level != self.trading_level_asc[0]:
                raise Exception("trader level should be the min of the selectors")

            self.trading_level_desc = list(self.trading_level_asc)
            self.trading_level_desc.reverse()

        self.session = get_db_session('zvt', data_schema=TraderInfo)

        self.level_map_long_targets = {}
        self.level_map_short_targets = {}

        self.on_start()

    def on_start(self):
        # run all the selectors
        for selector in self.selectors:
            # run for the history data at first
            selector.run()

        if self.entity_ids:
            entity_ids = json.dumps(self.entity_ids)
        else:
            entity_ids = None

        if self.exchanges:
            exchanges = json.dumps(self.exchanges)
        else:
            exchanges = None

        if self.codes:
            codes = json.dumps(self.codes)
        else:
            codes = None

        sim_account = TraderInfo(id=self.trader_name,
                                 entity_id=f'trader_zvt_{self.trader_name}',
                                 timestamp=self.start_timestamp,
                                 trader_name=self.trader_name,
                                 entity_ids=entity_ids,
                                 exchanges=exchanges,
                                 codes=codes,
                                 start_timestamp=self.start_timestamp,
                                 end_timestamp=self.end_timestamp,
                                 provider=self.provider,
                                 level=self.level.value,
                                 real_time=self.real_time,
                                 kdata_use_begin_time=self.kdata_use_begin_time)
        self.session.add(sim_account)
        self.session.commit()

    def init_selectors(self, entity_ids, entity_schema, exchanges, codes, start_timestamp, end_timestamp):
        """
        implement this to init selectors

        """
        pass

    def add_trading_signal_listener(self, listener):
        if listener not in self.trading_signal_listeners:
            self.trading_signal_listeners.append(listener)

    def remove_trading_signal_listener(self, listener):
        if listener in self.trading_signal_listeners:
            self.trading_signal_listeners.remove(listener)

    def handle_targets(self, due_timestamp: pd.Timestamp, happen_timestamp: pd.Timestamp):
        """
        this function would be called in every cycle, you could overwrite it for your custom algorithm to select the
        targets of different levels

        the default implementation is selecting the targets in all level

        :param due_timestamp:
        :param happen_timestamp:

        """
        long_selected = None
        short_selected = None
        for level in self.trading_level_desc:
            long_targets = self.level_map_long_targets.get(level)
            if long_targets:
                long_targets = set(long_targets)
                if not long_selected:
                    long_selected = long_targets
                else:
                    long_selected = long_selected & long_targets

            short_targets = self.level_map_short_targets.get(level)
            if short_targets:
                short_targets = set(short_targets)
                if not short_selected:
                    short_selected = short_targets
                else:
                    short_selected = short_selected & short_targets

        self.logger.debug('timestamp:{},long_selected:{}'.format(due_timestamp, long_selected))

        self.logger.debug('timestamp:{},short_selected:{}'.format(due_timestamp, short_selected))

        self.trade_the_targets(due_timestamp=due_timestamp, happen_timestamp=happen_timestamp,
                               long_selected=long_selected, short_selected=short_selected)

    def get_current_account(self) -> AccountStats:
        return self.account_service.account

    def buy(self, due_timestamp, happen_timestamp, entity_ids, position_pct=1.0, ignore_in_position=True):
        if ignore_in_position:
            account = self.get_current_account()
            current_holdings = []
            if account.positions:
                current_holdings = [position.entity_id for position in account.positions if position != None and
                                    position.available_long > 0]

            entity_ids = set(entity_ids) - set(current_holdings)

        if entity_ids:
            position_pct = (1.0 / len(entity_ids)) * position_pct

        for entity_id in entity_ids:
            trading_signal = TradingSignal(entity_id=entity_id,
                                           due_timestamp=due_timestamp,
                                           happen_timestamp=happen_timestamp,
                                           trading_signal_type=TradingSignalType.open_long,
                                           trading_level=self.level,
                                           position_pct=position_pct)
            self.send_trading_signal(trading_signal)

    def sell(self, due_timestamp, happen_timestamp, entity_ids, position_pct=1.0):
        # current position
        account = self.get_current_account()
        current_holdings = []
        if account.positions:
            current_holdings = [position.entity_id for position in account.positions if position != None and
                                position.available_long > 0]

        shorted = set(current_holdings) & entity_ids

        for entity_id in shorted:
            trading_signal = TradingSignal(entity_id=entity_id,
                                           due_timestamp=due_timestamp,
                                           happen_timestamp=happen_timestamp,
                                           trading_signal_type=TradingSignalType.close_long,
                                           trading_level=self.level,
                                           position_pct=position_pct)
            self.send_trading_signal(trading_signal)

    def trade_the_targets(self, due_timestamp, happen_timestamp, long_selected, short_selected, long_pct=1.0,
                          short_pct=1.0):
        if long_selected:
            self.buy(due_timestamp=due_timestamp, happen_timestamp=happen_timestamp, entity_ids=long_selected,
                     position_pct=long_pct)

        if short_selected:
            self.sell(due_timestamp=due_timestamp, happen_timestamp=happen_timestamp, entity_ids=short_selected,
                      position_pct=short_pct)

    def send_trading_signal(self, signal: TradingSignal):
        for listener in self.trading_signal_listeners:
            try:
                listener.on_trading_signal(signal)
            except Exception as e:
                self.logger.exception(e)
                listener.on_trading_error(timestamp=signal.happen_timestamp, error=e)

    def on_finish(self):
        # show the result
        if self.draw_result:
            import plotly.io as pio
            pio.renderers.default = "browser"
            reader = AccountStatsReader(trader_names=[self.trader_name])
            df = reader.data_df
            drawer = Drawer(main_data=NormalData(df.copy()[['trader_name', 'timestamp', 'all_value']],
                                                 category_field='trader_name'))
            drawer.draw_line(show=True)

    def select_long_targets(self, long_targets: List[str]) -> List[str]:
        if len(long_targets) > 10:
            return long_targets[0:10]
        return long_targets

    def select_short_targets(self, short_targets: List[str]) -> List[str]:
        if len(short_targets) > 10:
            return short_targets[0:10]
        return short_targets

    def in_trading_date(self, timestamp):
        return to_time_str(timestamp) in self.trading_dates

    def on_time(self, timestamp):
        self.logger.debug(f'current timestamp:{timestamp}')

    def input_long_targets(self, level, targets):
        logger.debug(f'level:{level},old long targets:{self.level_map_long_targets.get(level)},new long targets:{targets}')
        self.level_map_long_targets[level] = targets

    def input_short_targets(self, level, targets):
        logger.debug(
            f'level:{level},old short targets:{self.level_map_short_targets.get(level)},new short targets:{targets}')
        self.level_map_short_targets[level] = targets

    def run(self):
        # iterate timestamp of the min level,e.g,9:30,9:35,9.40...for 5min level
        # timestamp represents the timestamp in kdata
        for timestamp in self.entity_schema.get_interval_timestamps(start_date=self.start_timestamp,
                                                                    end_date=self.end_timestamp, level=self.level):

            if not self.in_trading_date(timestamp=timestamp):
                continue

            if self.real_time:
                # all selector move on to handle the coming data
                if self.kdata_use_begin_time:
                    real_end_timestamp = timestamp + pd.Timedelta(seconds=self.level.to_second())
                else:
                    real_end_timestamp = timestamp

                seconds = (now_pd_timestamp() - real_end_timestamp).total_seconds()
                waiting_seconds = self.level.to_second() - seconds
                # meaning the future kdata not ready yet,we could move on to check
                if waiting_seconds > 0:
                    # iterate the selector from min to max which in finished timestamp kdata
                    for level in self.trading_level_asc:
                        if self.entity_schema.is_finished_kdata_timestamp(timestamp=timestamp, level=level):
                            for selector in self.selectors:
                                if selector.level == level:
                                    selector.move_on(timestamp, self.kdata_use_begin_time, timeout=waiting_seconds + 20)

            # on_trading_open to setup the account
            if self.level == IntervalLevel.LEVEL_1DAY or (
                    self.level != IntervalLevel.LEVEL_1DAY and self.entity_schema.is_open_timestamp(timestamp)):
                self.account_service.on_trading_open(timestamp)

            self.on_time(timestamp=timestamp)

            if self.selectors:
                for level in self.trading_level_asc:
                    # in every cycle, all level selector do its job in its time
                    if self.entity_schema.is_finished_kdata_timestamp(timestamp=timestamp, level=level):
                        all_long_targets = []
                        all_short_targets = []
                        for selector in self.selectors:
                            if selector.level == level:
                                long_targets = selector.get_open_long_targets(timestamp=timestamp)
                                long_targets = self.select_long_targets(long_targets)

                                short_targets = selector.get_open_short_targets(timestamp=timestamp)
                                short_targets = self.select_short_targets(short_targets)

                                all_long_targets += long_targets
                                all_short_targets += short_targets

                        if all_long_targets:
                            self.input_long_targets(level, all_long_targets)
                        if all_short_targets:
                            self.input_short_targets(level, all_short_targets)

                        # the time always move on by min level step and we could check all targets of levels
                        # 1)the targets is generated for next interval
                        # 2)the acceptable price is next interval prices,you could buy it at current price
                        # if the time is before the timestamp(due_timestamp) when trading signal received
                        # 3)the suggest price the the close price for generating the signal(happen_timestamp)
                        due_timestamp = timestamp + pd.Timedelta(seconds=self.level.to_second())
                        if level == self.level:
                            self.handle_targets(due_timestamp=due_timestamp, happen_timestamp=timestamp)

            # on_trading_close to calculate date account
            if self.level == IntervalLevel.LEVEL_1DAY or (
                    self.level != IntervalLevel.LEVEL_1DAY and self.entity_schema.is_close_timestamp(timestamp)):
                self.account_service.on_trading_close(timestamp)

        self.on_finish()


class StockTrader(Trader):
    entity_schema = Stock
