# -*- coding: utf-8 -*-
import json
import logging
from typing import List, Union

import pandas as pd

from zvdata import IntervalLevel
from zvdata.contract import get_db_session
from zvdata.normal_data import NormalData
from zvdata.utils.time_utils import to_pd_timestamp, now_pd_timestamp
from zvt.api.business import get_trader
from zvt.api.common import get_one_day_trading_minutes, decode_entity_id
from zvt.api.rules import iterate_timestamps, is_open_time, is_in_finished_timestamps, is_close_time, is_trading_date
from zvt.domain import business
from zvt.drawer.drawer import Drawer
from zvt.factors.target_selector import TargetSelector
from zvt.reader.business_reader import AccountReader
from zvt.trader import TradingSignal, TradingSignalType
from zvt.trader.account import SimAccountService

logger = logging.getLogger(__name__)


# overwrite it to custom your selector comparator
class SelectorsComparator(object):

    def __init__(self, selectors: List[TargetSelector]) -> None:
        self.selectors: List[TargetSelector] = selectors

    def make_decision(self, timestamp, trading_level: IntervalLevel):
        """

        :param timestamp:
        :type timestamp:
        :param trading_level:
        :type trading_level: zvt.domain.common.IntervalLevel
        """
        raise NotImplementedError


# a selector comparator select the targets ordered by score and limit the targets number
class LimitSelectorsComparator(SelectorsComparator):

    def __init__(self, selectors: List[TargetSelector], limit=10) -> None:
        super().__init__(selectors)
        self.limit = limit

    def make_decision(self, timestamp, trading_level: IntervalLevel):
        logger.debug('current timestamp:{}'.format(timestamp))

        all_long_targets = []
        all_short_targets = []
        for selector in self.selectors:
            if selector.level == trading_level:
                long_targets = selector.get_open_long_targets(timestamp=timestamp)
                short_targets = selector.get_open_short_targets(timestamp=timestamp)
                if long_targets:
                    logger.debug(
                        '{} selector:{} make_decision,long_targets size:{}'.format(trading_level.value, selector,
                                                                                   len(long_targets)))
                    if len(long_targets) > self.limit:
                        long_targets = long_targets[0:self.limit]
                        logger.debug('{} selector:{} make_decision,keep:{}'.format(trading_level.value, selector,
                                                                                   len(long_targets)))
                if short_targets:
                    logger.debug(
                        '{} selector:{} make_decision, short_targets size:{}'.format(trading_level.value, selector,
                                                                                     len(short_targets)))
                    if len(short_targets) > self.limit:
                        short_targets = short_targets[0:self.limit]
                        logger.debug('{} selector:{} make_decision,keep:{}'.format(trading_level.value, selector,
                                                                                   len(short_targets)))

                all_long_targets += long_targets
                all_short_targets += short_targets

        return all_long_targets, all_short_targets


# the data structure for storing level:targets map,you should handle the targets of the level before overwrite it
class TargetsSlot(object):

    def __init__(self) -> None:
        self.level_map_targets = {}

    def input_targets(self, level: IntervalLevel, long_targets: List[str], short_targets: List[str]):
        logger.debug('level:{},old targets:{},new targets:{}'.format(level,
                                                                     self.get_targets(level),
                                                                     (long_targets, short_targets)))
        self.level_map_targets[level.value] = (long_targets, short_targets)

    def get_targets(self, level: IntervalLevel):
        return self.level_map_targets.get(level.value)


class Trader(object):
    logger = logging.getLogger(__name__)

    entity_type: str = None

    def __init__(self,
                 entity_ids: List[str] = None,
                 exchanges: List[str] = ['sh', 'sz'],
                 codes: List[str] = None,
                 start_timestamp: Union[str, pd.Timestamp] = None,
                 end_timestamp: Union[str, pd.Timestamp] = None,
                 provider: str = 'joinquant',
                 level: Union[str, IntervalLevel] = IntervalLevel.LEVEL_1DAY,
                 trader_name: str = None,
                 real_time: bool = False,
                 kdata_use_begin_time: bool = False) -> None:

        assert self.entity_type is not None

        if trader_name:
            self.trader_name = trader_name
        else:
            self.trader_name = type(self).__name__.lower()

        self.trading_signal_listeners = []

        self.selectors: List[TargetSelector] = []

        self.entity_ids = entity_ids

        self.exchanges = exchanges
        self.codes = codes

        # FIXME:handle this case gracefully
        if self.entity_ids:
            entity_type, exchange, code = decode_entity_id(self.entity_ids[0])
            if not self.entity_type:
                self.entity_type = entity_type
            if not self.exchanges:
                self.exchanges = [exchange]

        self.provider = provider
        # make sure the min level selector correspond to the provider and level
        self.level = IntervalLevel(level)
        self.real_time = real_time

        if start_timestamp and end_timestamp:
            self.start_timestamp = to_pd_timestamp(start_timestamp)
            self.end_timestamp = to_pd_timestamp(end_timestamp)
        else:
            assert False

        if real_time:
            logger.info(
                'real_time mode, end_timestamp should be future,you could set it big enough for running forever')
            assert self.end_timestamp >= now_pd_timestamp()

        self.kdata_use_begin_time = kdata_use_begin_time

        self.account_service = SimAccountService(trader_name=self.trader_name,
                                                 timestamp=self.start_timestamp,
                                                 provider=self.provider,
                                                 level=self.level)

        self.add_trading_signal_listener(self.account_service)

        self.init_selectors(entity_ids=entity_ids, entity_type=self.entity_type, exchanges=self.exchanges,
                            codes=self.codes, start_timestamp=self.start_timestamp, end_timestamp=self.end_timestamp)

        self.selectors_comparator = self.init_selectors_comparator()

        self.trading_level_asc = list(set([IntervalLevel(selector.level) for selector in self.selectors]))
        self.trading_level_asc.sort()

        self.trading_level_desc = list(self.trading_level_asc)
        self.trading_level_desc.reverse()

        self.targets_slot: TargetsSlot = TargetsSlot()

        self.session = get_db_session('zvt', 'business')
        trader = get_trader(session=self.session, trader_name=self.trader_name, return_type='domain', limit=1)

        if trader:
            self.logger.warning("trader:{} has run before,old result would be deleted".format(self.trader_name))
            self.session.query(business.Trader).filter(business.Trader.trader_name == self.trader_name).delete()
            self.session.commit()
        self.on_start()

    def on_start(self):
        if not self.selectors:
            raise Exception('please setup self.selectors in init_selectors at first')

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

        trader_domain = business.Trader(id=self.trader_name, timestamp=self.start_timestamp,
                                        trader_name=self.trader_name,
                                        entity_type=entity_ids, exchanges=exchanges, codes=codes,
                                        start_timestamp=self.start_timestamp,
                                        end_timestamp=self.end_timestamp, provider=self.provider,
                                        level=self.level.value,
                                        real_time=self.real_time, kdata_use_begin_time=self.kdata_use_begin_time)
        self.session.add(trader_domain)
        self.session.commit()

    def init_selectors(self, entity_ids, entity_type, exchanges, codes, start_timestamp, end_timestamp):
        """
        implement this to init selectors

        """
        raise NotImplementedError

    def init_selectors_comparator(self):
        """
        overwrite this to set selectors_comparator

        """
        return LimitSelectorsComparator(self.selectors)

    def add_trading_signal_listener(self, listener):
        if listener not in self.trading_signal_listeners:
            self.trading_signal_listeners.append(listener)

    def remove_trading_signal_listener(self, listener):
        if listener in self.trading_signal_listeners:
            self.trading_signal_listeners.remove(listener)

    def handle_targets_slot(self, timestamp):
        """
        this function would be called in every cycle, you could overwrite it for your custom algorithm to select the
        targets of different levels

        the default implementation is selecting the targets in all levels

        :param timestamp:
        :type timestamp:
        """
        long_selected = None
        short_selected = None
        for level in self.trading_level_desc:
            targets = self.targets_slot.get_targets(level=level)
            if targets:
                long_targets = set(targets[0])
                short_targets = set(targets[1])

                if not long_selected:
                    long_selected = long_targets
                else:
                    long_selected = long_selected & long_targets

                if not short_selected:
                    short_selected = short_targets
                else:
                    short_selected = short_selected & short_targets

        self.logger.debug('timestamp:{},long_selected:{}'.format(timestamp, long_selected))

        self.logger.debug('timestamp:{},short_selected:{}'.format(timestamp, short_selected))

        self.send_trading_signals(timestamp=timestamp, long_selected=long_selected, short_selected=short_selected)

    def send_trading_signals(self, timestamp, long_selected, short_selected):
        # current position
        account = self.account_service.latest_account
        current_holdings = [position['entity_id'] for position in account['positions'] if
                            position['available_long'] > 0]

        if long_selected:
            # just long the security not in the positions
            longed = long_selected - set(current_holdings)
            if longed:
                position_pct = 1.0 / len(longed)
                order_money = account['cash'] * position_pct

                for entity_id in longed:
                    trading_signal = TradingSignal(entity_id=entity_id,
                                                   the_timestamp=timestamp,
                                                   trading_signal_type=TradingSignalType.trading_signal_open_long,
                                                   trading_level=self.level,
                                                   order_money=order_money)
                    for listener in self.trading_signal_listeners:
                        listener.on_trading_signal(trading_signal)

        # just short the security in current_holdings and short_selected
        if short_selected:
            shorted = set(current_holdings) & short_selected

            for entity_id in shorted:
                trading_signal = TradingSignal(entity_id=entity_id,
                                               the_timestamp=timestamp,
                                               trading_signal_type=TradingSignalType.trading_signal_close_long,
                                               position_pct=1.0,
                                               trading_level=self.level)
                for listener in self.trading_signal_listeners:
                    listener.on_trading_signal(trading_signal)

    def on_finish(self):
        # show the result
        import plotly.io as pio
        pio.renderers.default = "browser"
        reader = AccountReader(trader_names=[self.trader_name])
        drawer = Drawer(main_data=NormalData(reader.data_df.copy()[['trader_name', 'timestamp', 'all_value']],
                                             category_field='trader_name'))
        drawer.draw_line()

    def run(self):
        # iterate timestamp of the min level,e.g,9:30,9:35,9.40...for 5min level
        # timestamp represents the timestamp in kdata
        for timestamp in iterate_timestamps(entity_type=self.entity_type, exchange=self.exchanges[0],
                                            start_timestamp=self.start_timestamp, end_timestamp=self.end_timestamp,
                                            level=self.level):

            if not is_trading_date(entity_type=self.entity_type, exchange=self.exchanges[0], timestamp=timestamp):
                continue
            if self.real_time:
                # all selector move on to handle the coming data
                if self.kdata_use_begin_time:
                    real_end_timestamp = timestamp + pd.Timedelta(seconds=self.level.to_second())
                else:
                    real_end_timestamp = timestamp

                waiting_seconds, _ = self.level.count_from_timestamp(real_end_timestamp,
                                                                     one_day_trading_minutes=get_one_day_trading_minutes(
                                                                         entity_type=self.entity_type))
                # meaning the future kdata not ready yet,we could move on to check
                if waiting_seconds and (waiting_seconds > 0):
                    # iterate the selector from min to max which in finished timestamp kdata
                    for level in self.trading_level_asc:
                        if (is_in_finished_timestamps(entity_type=self.entity_type, exchange=self.exchanges[0],
                                                      timestamp=timestamp, level=level)):
                            for selector in self.selectors:
                                if selector.level == level:
                                    selector.move_on(timestamp, self.kdata_use_begin_time, timeout=waiting_seconds + 20)

            # on_trading_open to setup the account
            if self.level == IntervalLevel.LEVEL_1DAY or (
                    self.level != IntervalLevel.LEVEL_1DAY and is_open_time(entity_type=self.entity_type,
                                                                            exchange=self.exchanges[0],
                                                                            timestamp=timestamp)):
                self.account_service.on_trading_open(timestamp)

            # the time always move on by min level step and we could check all level targets in the slot
            self.handle_targets_slot(timestamp=timestamp)

            for level in self.trading_level_asc:
                # in every cycle, all level selector do its job in its time
                if (is_in_finished_timestamps(entity_type=self.entity_type, exchange=self.exchanges[0],
                                              timestamp=timestamp, level=level)):
                    long_targets, short_targets = self.selectors_comparator.make_decision(timestamp=timestamp,
                                                                                          trading_level=level)

                    self.targets_slot.input_targets(level, long_targets, short_targets)

            # on_trading_close to calculate date account
            if self.level == IntervalLevel.LEVEL_1DAY or (
                    self.level != IntervalLevel.LEVEL_1DAY and is_close_time(entity_type=self.entity_type,
                                                                             exchange=self.exchanges[0],
                                                                             timestamp=timestamp)):
                self.account_service.on_trading_close(timestamp)

        self.on_finish()


class StockTrader(Trader):
    entity_type = 'stock'


class CoinTrader(Trader):
    entity_type = 'coin'
