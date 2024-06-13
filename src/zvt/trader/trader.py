# -*- coding: utf-8 -*-
import logging
import time
from typing import List, Union, Type, Tuple

import pandas as pd

from zvt.contract import IntervalLevel, TradableEntity, AdjustType
from zvt.contract.drawer import Drawer
from zvt.contract.factor import Factor, TargetType
from zvt.contract.normal_data import NormalData
from zvt.domain import Stock
from zvt.trader import TradingSignal, TradingSignalType, TradingListener
from zvt.trader.sim_account import SimAccountService
from zvt.trader.trader_info_api import AccountStatsReader
from zvt.trader.trader_schemas import AccountStats, Position
from zvt.utils.time_utils import to_pd_timestamp, now_pd_timestamp, to_time_str, is_same_date, date_time_by_interval


class Trader(object):
    entity_schema: Type[TradableEntity] = None

    def __init__(
        self,
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
        draw_result: bool = True,
        rich_mode: bool = False,
        adjust_type: AdjustType = None,
        profit_threshold=(3, -0.3),
        keep_history=False,
        pre_load_days=365,
    ) -> None:
        assert self.entity_schema is not None
        assert start_timestamp is not None
        assert end_timestamp is not None

        self.logger = logging.getLogger(__name__)

        if trader_name:
            self.trader_name = trader_name
        else:
            self.trader_name = type(self).__name__.lower()

        self.entity_ids = entity_ids
        self.exchanges = exchanges
        self.codes = codes
        self.provider = provider
        # make sure the min level factor correspond to the provider and level
        self.level = IntervalLevel(level)
        self.real_time = real_time
        self.start_timestamp = to_pd_timestamp(start_timestamp)
        self.end_timestamp = to_pd_timestamp(end_timestamp)
        self.pre_load_days = pre_load_days

        self.trading_dates = self.entity_schema.get_trading_dates(
            start_date=self.start_timestamp, end_date=self.end_timestamp
        )

        if real_time:
            self.logger.info(
                "real_time mode, end_timestamp should be future,you could set it big enough for running forever"
            )
            assert self.end_timestamp >= now_pd_timestamp()

        # false: 收到k线时，该k线已完成
        # true: 收到k线时，该k线可能未完成
        self.kdata_use_begin_time = kdata_use_begin_time
        self.draw_result = draw_result
        self.rich_mode = rich_mode

        self.adjust_type = AdjustType(adjust_type)
        self.profit_threshold = profit_threshold
        self.keep_history = keep_history

        self.level_map_long_targets = {}
        self.level_map_short_targets = {}
        self.trading_signals: List[TradingSignal] = []
        self.trading_signal_listeners: List[TradingListener] = []

        self.account_service = SimAccountService(
            entity_schema=self.entity_schema,
            trader_name=self.trader_name,
            timestamp=self.start_timestamp,
            provider=self.provider,
            level=self.level,
            rich_mode=self.rich_mode,
            adjust_type=self.adjust_type,
            keep_history=self.keep_history,
        )

        self.register_trading_signal_listener(self.account_service)

        self.factors = self.init_factors(
            entity_ids=self.entity_ids,
            entity_schema=self.entity_schema,
            exchanges=self.exchanges,
            codes=self.codes,
            start_timestamp=date_time_by_interval(self.start_timestamp, -self.pre_load_days),
            end_timestamp=self.end_timestamp,
            adjust_type=self.adjust_type,
        )

        if self.factors:
            self.trading_level_asc = list(set([IntervalLevel(factor.level) for factor in self.factors]))
            self.trading_level_asc.sort()

            self.logger.info(f"trader level:{self.level},factors level:{self.trading_level_asc}")

            if self.level != self.trading_level_asc[0]:
                raise Exception("trader level should be the min of the factors")

            self.trading_level_desc = list(self.trading_level_asc)
            self.trading_level_desc.reverse()
        else:
            self.trading_level_asc = [self.level]
            self.trading_level_desc = [self.level]
        self.on_init()

    def on_init(self):
        self.logger.info(f"trader:{self.trader_name} on_start")

    def init_entities(self, timestamp):
        """
        init the entities for timestamp

        :param timestamp:
        :return:
        """
        self.logger.info(f"timestamp: {timestamp} init_entities")
        return self.entity_ids

    def init_factors(
        self, entity_ids, entity_schema, exchanges, codes, start_timestamp, end_timestamp, adjust_type=None
    ):
        """
        overwrite it to init factors if you want to use factor computing model
        :param adjust_type:

        """
        return []

    def update_targets_by_level(
        self,
        level: IntervalLevel,
        long_targets: List[str],
        short_targets: List[str],
    ) -> None:
        """
        the trading signals is generated in min level,before that,we should cache targets of all levels

        :param level:
        :param long_targets:
        :param short_targets:
        """
        self.logger.debug(
            f"level:{level},old long targets:{self.level_map_long_targets.get(level)},new long targets:{long_targets}"
        )
        self.level_map_long_targets[level] = long_targets

        self.logger.debug(
            f"level:{level},old short targets:{self.level_map_short_targets.get(level)},new short targets:{short_targets}"
        )
        self.level_map_short_targets[level] = short_targets

    def get_long_targets_by_level(self, level: IntervalLevel) -> List[str]:
        return self.level_map_long_targets.get(level)

    def get_short_targets_by_level(self, level: IntervalLevel) -> List[str]:
        return self.level_map_short_targets.get(level)

    def on_targets_selected_from_levels(self, timestamp) -> Tuple[List[str], List[str]]:
        """
        this method's called in every min level cycle to select targets in all levels generated by the previous cycle
        the default implementation is selecting the targets in all levels
        overwrite it for your custom logic

        :param timestamp: current event time
        :return: long targets, short targets
        """

        long_selected = None

        short_selected = None

        for level in self.trading_level_desc:
            long_targets = self.level_map_long_targets.get(level)
            # long must in all
            if long_targets:
                long_targets = set(long_targets)
                if long_selected is None:
                    long_selected = long_targets
                else:
                    long_selected = long_selected & long_targets
            else:
                long_selected = set()

            short_targets = self.level_map_short_targets.get(level)
            # short any
            if short_targets:
                short_targets = set(short_targets)
                if short_selected is None:
                    short_selected = short_targets
                else:
                    short_selected = short_selected | short_targets

        return long_selected, short_selected

    def get_current_account(self) -> AccountStats:
        return self.account_service.get_current_account()

    def get_current_positions(self) -> List[Position]:
        return self.get_current_account().positions

    def long_position_control(self):
        positions = self.get_current_positions()

        position_pct = 1.0
        if not positions:
            # 没有仓位，买2成
            position_pct = 0.2
        elif len(positions) <= 10:
            # 小于10个持仓，买5成
            position_pct = 0.5

        # 买完
        return position_pct

    def short_position_control(self):
        # 卖完
        return 1.0

    def on_profit_control(self):
        if self.profit_threshold and self.get_current_positions():
            positive = self.profit_threshold[0]
            negative = self.profit_threshold[1]
            close_long_entity_ids = []
            for position in self.get_current_positions():
                if position.available_long > 1:
                    # 止盈
                    if position.profit_rate >= positive:
                        close_long_entity_ids.append(position.entity_id)
                        self.logger.info(f"close profit {position.profit_rate} for {position.entity_id}")
                    # 止损
                    if position.profit_rate <= negative:
                        close_long_entity_ids.append(position.entity_id)
                        self.logger.info(f"cut lost {position.profit_rate} for {position.entity_id}")

            return close_long_entity_ids, None
        return None, None

    def buy(self, timestamp, entity_ids, ignore_in_position=True):
        if ignore_in_position:
            account = self.get_current_account()
            current_holdings = []
            if account.positions:
                current_holdings = [
                    position.entity_id
                    for position in account.positions
                    if position != None and position.available_long > 0
                ]

            entity_ids = set(entity_ids) - set(current_holdings)

        if entity_ids:
            position_pct = self.long_position_control()
            position_pct = (1.0 / len(entity_ids)) * position_pct

            due_timestamp = to_pd_timestamp(timestamp) + pd.Timedelta(seconds=self.level.to_second())
            for entity_id in entity_ids:
                trading_signal = TradingSignal(
                    entity_id=entity_id,
                    due_timestamp=due_timestamp,
                    happen_timestamp=timestamp,
                    trading_signal_type=TradingSignalType.open_long,
                    trading_level=self.level,
                    position_pct=position_pct,
                )
                self.trading_signals.append(trading_signal)

    def sell(self, timestamp, entity_ids):
        # current position
        account = self.get_current_account()
        current_holdings = []
        if account.positions:
            current_holdings = [
                position.entity_id for position in account.positions if position != None and position.available_long > 0
            ]

        shorted = set(current_holdings) & set(entity_ids)

        if shorted:
            position_pct = self.short_position_control()

            due_timestamp = to_pd_timestamp(timestamp) + pd.Timedelta(seconds=self.level.to_second())
            for entity_id in shorted:
                trading_signal = TradingSignal(
                    entity_id=entity_id,
                    due_timestamp=due_timestamp,
                    happen_timestamp=timestamp,
                    trading_signal_type=TradingSignalType.close_long,
                    trading_level=self.level,
                    position_pct=position_pct,
                )
                self.trading_signals.append(trading_signal)

    def on_finish(self, timestamp):
        self.on_trading_finish(timestamp)
        # show the result
        if self.draw_result:
            reader = AccountStatsReader(trader_names=[self.trader_name])
            df = reader.data_df
            drawer = Drawer(
                main_data=NormalData(df.copy()[["trader_name", "timestamp", "all_value"]], category_field="trader_name")
            )
            drawer.draw_line(show=True)

    def on_factor_targets_filtered(
        self, timestamp, level, factor: Factor, long_targets: List[str], short_targets: List[str]
    ) -> Tuple[List[str], List[str]]:
        """
        overwrite it to filter the targets from factor

        :param timestamp: the event time
        :param level: the level
        :param factor: the factor
        :param long_targets: the long targets from the factor
        :param short_targets: the short targets from the factor
        :return: filtered long targets, filtered short targets
        """
        self.logger.info(f"on_targets_filtered {level} long:{long_targets}")

        if len(long_targets) > 10:
            long_targets = long_targets[0:10]
        self.logger.info(f"on_targets_filtered {level} filtered long:{long_targets}")

        return long_targets, short_targets

    def in_trading_date(self, timestamp):
        return to_time_str(timestamp) in self.trading_dates

    def on_time(self, timestamp: pd.Timestamp):
        """
        called in every min level cycle

        :param timestamp: event time
        """
        self.logger.debug(f"current timestamp:{timestamp}")

    def on_trading_signals(self, trading_signals: List[TradingSignal]):
        for l in self.trading_signal_listeners:
            l.on_trading_signals(trading_signals)
        # clear after all listener handling
        self.trading_signals = []

    def on_trading_open(self, timestamp):
        for l in self.trading_signal_listeners:
            l.on_trading_open(timestamp)

    def on_trading_close(self, timestamp):
        for l in self.trading_signal_listeners:
            l.on_trading_close(timestamp)

    def on_trading_finish(self, timestamp):
        for l in self.trading_signal_listeners:
            l.on_trading_finish(timestamp)

    def on_trading_error(self, timestamp, error):
        for l in self.trading_signal_listeners:
            l.on_trading_error(timestamp, error)

    def on_non_trading_day(self, timestamp):
        self.logger.info(f"on_non_trading_day: {timestamp}")

    def get_factors_by_level(self, level):
        return [factor for factor in self.factors if factor.level == level]

    def handle_factor_targets(self, timestamp: pd.Timestamp):
        """
        select targets from factors
        :param timestamp: the timestamp for next kdata coming
        """
        # 一般来说factor计算 多标的 历史数据比较快，多级别的计算也比较方便，常用于全市场标的粗过滤
        # 更细节的控制可以在on_targets_filtered里进一步处理
        # 也可以在on_time里面设计一些自己的逻辑配合过滤
        # 多级别的遍历算法要点:
        # 1)计算各级别的 标的，通过 on_factor_targets_filtered 过滤，缓存在level_map_long_targets，level_map_short_targets
        # 2)在最小的level通过 on_targets_selected_from_levels 根据多级别的缓存标的，生成最终的选中标的
        # 这里需要注意的是，小级别拿到上一个周期的大级别的标的，这是合理的
        for level in self.trading_level_asc:
            self.logger.info(f"level: {level}")
            # in every cycle, all level factor do its job in its time
            if self.entity_schema.is_finished_kdata_timestamp(timestamp=timestamp, level=level):
                all_long_targets = []
                all_short_targets = []

                # 从该level的factor中过滤targets
                current_level_factors = self.get_factors_by_level(level=level)
                for factor in current_level_factors:
                    long_targets = factor.get_targets(timestamp=timestamp, target_type=TargetType.positive)
                    short_targets = factor.get_targets(timestamp=timestamp, target_type=TargetType.negative)

                    if long_targets or short_targets:
                        long_targets, short_targets = self.on_factor_targets_filtered(
                            timestamp=timestamp,
                            level=level,
                            factor=factor,
                            long_targets=long_targets,
                            short_targets=short_targets,
                        )

                    if long_targets:
                        all_long_targets += long_targets
                    if short_targets:
                        all_short_targets += short_targets

                # 将各级别的targets缓存在level_map_long_targets，level_map_short_targets
                self.update_targets_by_level(level, all_long_targets, all_short_targets)

    def run(self):
        # iterate timestamp of the min level,e.g,9:30,9:35,9.40...for 5min level
        # timestamp represents the timestamp in kdata
        for timestamp in self.entity_schema.get_interval_timestamps(
            start_date=self.start_timestamp, end_date=self.end_timestamp, level=self.level
        ):
            self.logger.info(f">>>>>>>>>>")

            self.entity_ids = self.init_entities(timestamp=timestamp)
            self.logger.info(f"current entities: {self.entity_ids}")

            if not self.in_trading_date(timestamp=timestamp):
                self.on_non_trading_day(timestamp=timestamp)
                continue

            # on_trading_open to set the account
            if self.level >= IntervalLevel.LEVEL_1DAY or (
                self.level != IntervalLevel.LEVEL_1DAY and self.entity_schema.is_open_timestamp(timestamp)
            ):
                self.on_trading_open(timestamp=timestamp)

            # the signals were generated by previous timestamp kdata
            if self.trading_signals:
                self.logger.info("current signals:")
                for signal in self.trading_signals:
                    self.logger.info(str(signal))
                self.on_trading_signals(self.trading_signals)

            for factor in self.factors:
                factor.add_entities(entity_ids=self.entity_ids)

            waiting_seconds = 0

            if self.level == IntervalLevel.LEVEL_1DAY:
                if is_same_date(timestamp, now_pd_timestamp()):
                    while True:
                        self.logger.info(f"time is:{now_pd_timestamp()},just smoke for minutes")
                        time.sleep(600)
                        current = now_pd_timestamp()
                        if current.hour >= 19:
                            waiting_seconds = 20
                            break

            elif self.real_time:
                # all factor move on to handle the coming data
                if self.kdata_use_begin_time:
                    real_end_timestamp = timestamp + pd.Timedelta(seconds=self.level.to_second())
                else:
                    real_end_timestamp = timestamp

                seconds = (now_pd_timestamp() - real_end_timestamp).total_seconds()
                waiting_seconds = self.level.to_second() - seconds

            # meaning the future kdata not ready yet,we could move on to check
            if waiting_seconds > 0:
                # iterate the factor from min to max which in finished timestamp kdata
                for level in self.trading_level_asc:
                    if self.entity_schema.is_finished_kdata_timestamp(timestamp=timestamp, level=level):
                        factors = self.get_factors_by_level(level=level)
                        for factor in factors:
                            factor.move_on(to_timestamp=timestamp, timeout=waiting_seconds + 20)

            if self.factors:
                self.handle_factor_targets(timestamp=timestamp)

            self.on_time(timestamp=timestamp)

            long_selected, short_selected = self.on_targets_selected_from_levels(timestamp)

            # 处理 止赢 止损
            passive_short, _ = self.on_profit_control()
            if passive_short:
                if not short_selected:
                    short_selected = passive_short
                else:
                    short_selected = list(set(short_selected) | set(passive_short))

            if short_selected:
                self.sell(timestamp=timestamp, entity_ids=short_selected)
            if long_selected:
                self.buy(timestamp=timestamp, entity_ids=long_selected)

            # on_trading_close to calculate date account
            if self.level >= IntervalLevel.LEVEL_1DAY or (
                self.level != IntervalLevel.LEVEL_1DAY and self.entity_schema.is_close_timestamp(timestamp)
            ):
                self.on_trading_close(timestamp)

            self.logger.info(f"<<<<<<<<<<\n")

        self.on_finish(timestamp)

    def register_trading_signal_listener(self, listener):
        if listener not in self.trading_signal_listeners:
            self.trading_signal_listeners.append(listener)

    def deregister_trading_signal_listener(self, listener):
        if listener in self.trading_signal_listeners:
            self.trading_signal_listeners.remove(listener)


class StockTrader(Trader):
    entity_schema = Stock

    def __init__(
        self,
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
        draw_result: bool = True,
        rich_mode: bool = False,
        adjust_type: AdjustType = AdjustType.hfq,
        profit_threshold=(3, -0.3),
        keep_history=False,
    ) -> None:
        super().__init__(
            entity_ids,
            exchanges,
            codes,
            start_timestamp,
            end_timestamp,
            provider,
            level,
            trader_name,
            real_time,
            kdata_use_begin_time,
            draw_result,
            rich_mode,
            adjust_type,
            profit_threshold,
            keep_history,
        )


# the __all__ is generated
__all__ = ["Trader", "StockTrader"]
