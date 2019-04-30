# -*- coding: utf-8 -*-

import logging
import math
import queue
import threading

from zvt.api.account import get_account
from zvt.api.technical import get_kdata
from zvt.domain import get_db_session
from zvt.domain.account import SimAccount, Position
from zvt.trader import TradingSignalType, TradingSignalListener, TradingSignal
from zvt.trader.errors import NotEnoughMoneyError, InvalidOrderError, NotEnoughPositionError
from zvt.utils.time_utils import to_pd_timestamp

ORDER_TYPE_LONG = 'order_long'
ORDER_TYPE_SHORT = 'order_short'
ORDER_TYPE_CLOSE_LONG = 'order_close_long'
ORDER_TYPE_CLOSE_SHORT = 'order_close_short'


class AccountService(TradingSignalListener):
    logger = logging.getLogger(__name__)

    def get_current_position(self, security_id):
        pass

    def order(self, security_id, current_price, current_timestamp, order_amount=0, order_pct=1.0, order_price=0,
              order_type=ORDER_TYPE_LONG):
        pass

    # 开多,对于某些品种只能开多，比如中国股票
    def buy(self, security_id, current_price, current_timestamp, order_amount=0, order_pct=1.0, order_price=0):
        self.order(security_id, current_price, current_timestamp, order_amount, order_pct, order_price,
                   order_type=ORDER_TYPE_LONG)

    # 开空
    def sell(self, security_id, current_price, current_timestamp, order_amount=0, order_pct=1.0, order_price=0):
        self.order(security_id, current_price, current_timestamp, order_amount, order_pct, order_price,
                   order_type=ORDER_TYPE_SHORT)

    # 平多
    def close_long(self, security_id, current_price, current_timestamp, order_amount=0, order_pct=1.0, order_price=0):
        self.order(security_id, current_price, current_timestamp, order_amount, order_pct, order_price,
                   order_type=ORDER_TYPE_CLOSE_LONG)

    # 平空
    def close_short(self, security_id, current_price, current_timestamp, order_amount=0, order_pct=1.0, order_price=0):
        self.order(security_id, current_price, current_timestamp, order_amount, order_pct, order_price,
                   order_type=ORDER_TYPE_CLOSE_SHORT)

    @staticmethod
    def trading_signal_to_order_type(trading_signal_type):
        if trading_signal_type == TradingSignalType.trading_signal_open_long:
            return ORDER_TYPE_LONG
        if trading_signal_type == TradingSignalType.trading_signal_open_short:
            return ORDER_TYPE_SHORT
        if trading_signal_type == TradingSignalType.trading_signal_close_long:
            return ORDER_TYPE_CLOSE_LONG
        if trading_signal_type == TradingSignalType.trading_signal_close_short:
            return ORDER_TYPE_CLOSE_SHORT

    def on_trading_signal(self, trading_signal: TradingSignal):
        security_id = trading_signal.security_id
        current_price = trading_signal.current_price
        current_timestamp = trading_signal.start_timestamp
        order_type = AccountService.trading_signal_to_order_type(trading_signal.trading_signal_type)
        if order_type:
            try:
                self.order(security_id=security_id, current_price=current_price, current_timestamp=current_timestamp,
                           order_type=order_type)
            except Exception as e:
                self.logger.exception(e)


class SimAccountService(AccountService):
    account_queue = queue.Queue()

    def __init__(self, trader_name,
                 model_name,
                 timestamp,
                 base_capital=1000000,
                 buy_cost=0.001,
                 sell_cost=0.001,
                 slippage=0.001):

        self.base_capital = base_capital
        self.buy_cost = buy_cost
        self.sell_cost = sell_cost
        self.slippage = slippage
        self.trader_name = trader_name
        self.model_name = model_name

        self.session = get_db_session('trader')

        account = get_account(trader_name=self.trader_name, model_name=self.model_name, limit=1)

        if account:
            self.logger.warning("trader:{} has run before,old result would be deleted".format(trader_name))
            self.session.query(SimAccount).filter(SimAccount.trader_name == self.trader_name).delete()

        self.account = SimAccount()
        self.account.trader_name = trader_name
        self.account.model_name = model_name
        self.account.cash = self.base_capital
        self.account.positions = []
        self.account.all_value = self.base_capital
        self.account.value = 0
        self.account.timestamp = timestamp

        self.account_to_queue()

        t = threading.Thread(target=self.saving_account_worker)
        t.start()

    def account_to_queue(self):
        self.account_queue.put(self.account.to_dict(include_meta=True))

    def saving_account_worker(self):
        actions = []

        while True:
            try:
                account_json = self.account_queue.get(timeout=5)
                actions.append(account_json)
            except Exception as e:
                if actions:
                    while True:
                        resp = elasticsearch.helpers.bulk(es_client, actions)
                        self.logger.info(
                            "index to {} success:{} failed:{}".format("sim_account", resp[0], len(resp[1])))
                        if resp[1]:
                            self.logger.error("index to {} error:{}".format("sim_account", resp[1]))
                            continue
                        else:
                            actions = []
                            break

    def get_current_position(self, security_id):
        for position in self.account.positions:
            if position.securityId == security_id:
                return position

    # 计算收盘账户
    def calculate_closing_account(self, the_date):
        self.account.value = 0
        self.account.all_value = 0
        for position in self.account.positions:
            kdata = get_kdata(security_item=position['securityId'], the_date=the_date)
            closing_price = kdata['close']
            position.availableLong = position.longAmount
            position.availableShort = position.shortAmount

            if position.longAmount > 0:
                position.value = position.longAmount * closing_price
                self.account.value += position.value
            elif position.shortAmount > 0:
                position.value = 2 * (position.shortAmount * position.averageShortPrice)
                position.value -= position.shortAmount * closing_price
                self.account.value += position.value

        self.account.all_value = self.account.value + self.account.cash
        self.account.closing = True
        self.account.timestamp = the_date

        self.account_to_queue()

    def update_account(self, security_id, new_position, timestamp):
        # 先去掉之前的position
        positions = [position for position in self.account.positions if position.securityId != security_id]
        # 更新为新的position
        positions.append(new_position)
        self.account.positions = positions

        self.account.timestamp = to_pd_timestamp(timestamp)

        self.account_to_queue()

    def update_position(self, current_position, order_amount, current_price, order_type):
        if order_type == ORDER_TYPE_LONG:
            need_money = (order_amount * current_price) * (1 + self.slippage + self.buy_cost)
            if self.account.cash < need_money:
                raise NotEnoughMoneyError()

            self.account.cash -= need_money

            # 计算平均价
            long_amount = current_position.longAmount + order_amount
            current_position.averageLongPrice = (current_position.averageLongPrice * current_position.longAmount +
                                                 current_price * order_amount) / long_amount

            current_position.longAmount = long_amount

            if current_position.tradingT == 0:
                current_position.availableLong += order_amount

        elif order_type == ORDER_TYPE_SHORT:
            need_money = (order_amount * current_price) * (1 + self.slippage + self.buy_cost)
            if self.account.cash < need_money:
                raise NotEnoughMoneyError

            self.account.cash -= need_money

            short_amount = current_position.shortAmount + order_amount
            current_position.averageShortPrice = (current_position.averageShortPrice * current_position.shortAmount +
                                                  current_price * order_amount) / short_amount

            current_position.shortAmount = short_amount

            if current_position.tradingT == 0:
                current_position.availableShort += order_amount

        elif order_type == ORDER_TYPE_CLOSE_LONG:
            self.account.cash += (order_amount * current_price * (1 - self.slippage - self.sell_cost))

            current_position.availableLong -= order_amount
            current_position.longAmount -= order_amount

        elif order_type == ORDER_TYPE_CLOSE_SHORT:
            self.account.cash += 2 * (order_amount * current_position.averageShortPrice)
            self.account.cash -= order_amount * current_price * (1 + self.slippage + self.sell_cost)

            current_position.availableShort -= order_amount
            current_position.shortAmount -= order_amount

    def order(self, security_id, current_price, current_timestamp, order_amount=0, order_pct=1.0, order_price=0,
              order_type=ORDER_TYPE_LONG):
        """
        下单

        Parameters
        ----------
        security_id : str
            交易标的id

        current_price : float
            当前价格

        current_timestamp: timestamp
            下单的时间

        order_amount : int
            数量

        order_pct : float
            使用可用现金(仓位)的百分比,0.0-1.0

        order_price : float
            用于限价交易

        order_type : {ORDER_TYPE_LONG,ORDER_TYPE_SHORT,ORDER_TYPE_CLOSE_LONG,ORDER_TYPE_CLOSE_SHORT}
            交易类型

        Returns
        -------


        """

        # 市价交易,就是买卖是"当时"并"一定"能成交的
        # 简单起见，目前只支持这种方式
        if order_price == 0:
            current_position = self.get_current_position(security_id=security_id)
            if not current_position:
                current_position = Position(security_id=security_id)

            # 按数量交易
            if order_amount > 0:
                # 开多
                if order_type == ORDER_TYPE_LONG:
                    if current_position.short_amount > 0:
                        raise InvalidOrderError("close the short position before open long")

                    self.update_position(current_position, order_amount, current_price, order_type)
                # 开空
                elif order_type == ORDER_TYPE_SHORT:
                    if current_position.long_amount > 0:
                        raise InvalidOrderError("close the long position before open short")

                    self.update_position(current_position, order_amount, current_price, order_type)
                # 平多
                elif order_type == ORDER_TYPE_CLOSE_LONG:
                    if current_position.available_long >= order_amount:
                        self.update_position(current_position, order_amount, current_price, order_type)
                    else:
                        raise NotEnoughPositionError()
                # 平空
                elif order_type == ORDER_TYPE_CLOSE_SHORT:
                    if current_position.available_short >= order_amount:
                        self.update_position(current_position, order_amount, current_price, order_type)
                    else:
                        raise Exception("not enough position")

            # 按仓位比例交易
            elif 0 < order_pct <= 1:
                # 开多
                if order_type == ORDER_TYPE_LONG:
                    if current_position.short_amount > 0:
                        raise InvalidOrderError("close the short position before open long")

                    cost = current_price * (1 + self.slippage + self.buy_cost)
                    want_pay = self.account.cash * order_pct
                    # 买的数量
                    order_amount = want_pay // cost
                    if order_amount > 0:
                        self.update_position(current_position, order_amount, current_price, order_type)
                    else:
                        raise NotEnoughMoneyError()
                # 开空
                elif order_type == ORDER_TYPE_SHORT:
                    if current_position.long_amount > 0:
                        raise InvalidOrderError("close the long position before open short")

                    cost = current_price * (1 + self.slippage + self.buy_cost)
                    want_pay = self.account.cash * order_pct

                    order_amount = want_pay // cost
                    if order_amount > 0:
                        self.update_position(current_position, order_amount, current_price, order_type)
                    else:
                        raise NotEnoughMoneyError()

                # 平多
                elif order_type == ORDER_TYPE_CLOSE_LONG:
                    if current_position.available_long > 1:
                        if order_pct == 1.0:
                            order_amount = current_position.available_long
                        else:
                            order_amount = math.floor(current_position.available_long * order_pct)

                        if order_amount != 0:
                            self.update_position(current_position, order_amount, current_price, order_type)
                        else:
                            self.logger.warning("{} availableLong:{} order_pct:{} order_amount:{}", security_id,
                                                current_position.available_long, order_pct, order_amount)
                    else:
                        raise NotEnoughPositionError()
                # 平空
                elif order_type == ORDER_TYPE_CLOSE_SHORT:
                    if current_position.available_short > 1:
                        if order_pct == 1.0:
                            order_amount = current_position.available_short
                        else:
                            order_amount = math.floor(current_position.available_short * order_pct)

                        if order_amount != 0:
                            self.update_position(current_position, order_amount, current_price, order_type)
                        else:
                            self.logger.warning("{} availableLong:{} order_pct:{} order_amount:{}", security_id,
                                                current_position.available_long, order_pct, order_amount)
                    else:
                        raise Exception("not enough position")

            self.update_account(security_id, current_position, current_timestamp)
