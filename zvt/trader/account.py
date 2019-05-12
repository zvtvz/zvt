# -*- coding: utf-8 -*-

import logging
import math

from zvt.api.account import get_account
from zvt.api.technical import get_kdata
from zvt.domain import get_db_session, StoreCategory
from zvt.domain.account import SimAccount, Position
from zvt.trader import TradingSignalType, TradingSignalListener, TradingSignal
from zvt.trader.errors import NotEnoughMoneyError, InvalidOrderError, NotEnoughPositionError
from zvt.utils.time_utils import to_pd_timestamp, to_time_str, TIME_FORMAT_ISO8601

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
        current_timestamp = trading_signal.the_timestamp
        order_type = AccountService.trading_signal_to_order_type(trading_signal.trading_signal_type)
        trading_level = trading_signal.trading_level
        if order_type:
            try:
                kdata = get_kdata(provider=self.provider, security_id=security_id, level=trading_level,
                                  start_timestamp=current_timestamp,
                                  limit=1)
                if not kdata.empty and kdata['close'][0]:
                    self.order(security_id=security_id, current_price=kdata['close'][0],
                               current_timestamp=current_timestamp,
                               order_type=order_type,
                               order_pct=trading_signal.position_pct)
                else:
                    self.logger.warning(
                        'could not get kdata,security_id:{},timestamp:{}'.format(security_id, current_timestamp))
            except Exception as e:
                self.logger.exception(e)


class SimAccountService(AccountService):

    def __init__(self, trader_name,
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

        self.session = get_db_session('zvt', StoreCategory.business)
        self.provider = 'netease'

        account = get_account(session=self.session, trader_name=self.trader_name, return_type='domain', limit=1)

        if account:
            self.logger.warning("trader:{} has run before,old result would be deleted".format(trader_name))
            self.session.query(SimAccount).filter(SimAccount.trader_name == self.trader_name).delete()
            self.session.query(Position).filter(Position.trader_name == self.trader_name).delete()

        self.latest_account = SimAccount(trader_name=self.trader_name, cash=self.base_capital,
                                         positions=[], all_value=self.base_capital, value=0, timestamp=timestamp)

        self.save_account(self.latest_account)

    def save_account(self, account: SimAccount):
        the_id = '{}_{}'.format(self.trader_name, to_time_str(account.timestamp, TIME_FORMAT_ISO8601))
        account_domain = get_account(session=self.session, trader_name=self.trader_name,
                                     filters=[SimAccount.id == the_id], return_type='domain')
        if account_domain:
            account_domain = account_domain[0]
        else:
            account_domain = SimAccount(id=the_id, trader_name=self.trader_name, cash=account.cash,
                                        positions=account.positions,
                                        all_value=account.all_value, value=account.value, timestamp=account.timestamp)

        self.session.add(account_domain)
        self.session.commit()

    def get_current_position(self, security_id):
        for position in self.latest_account.positions:
            if position.security_id == security_id:
                return position
        return None

    def get_account_at_time(self, timestamp):
        """

        :param timestamp:
        :type timestamp:
        :return:
        :rtype:SimAccount
        """
        return get_account(session=self.session, trader_name=self.trader_name, return_type='domain',
                           end_timestamp=timestamp, limit=1)[0]

    # 计算收盘账户
    def save_closing_account(self, the_date):
        self.latest_account.value = 0
        self.latest_account.all_value = 0
        for position in self.latest_account.positions:
            kdata = get_kdata(provider=self.provider, security_id=position.security_id, end_timestamp=the_date, limit=1)
            closing_price = kdata['close']
            position.available_long = position.long_amount
            position.available_short = position.short_amount

            if position.long_amount > 0:
                position.value = position.long_amount * closing_price
                self.latest_account.value += position.value
            elif position.short_amount > 0:
                position.value = 2 * (position.short_amount * position.average_short_price)
                position.value -= position.short_amount * closing_price
                self.latest_account.value += position.value

        self.latest_account.all_value = self.latest_account.value + self.latest_account.cash
        self.latest_account.closing = True
        self.latest_account.timestamp = to_pd_timestamp(the_date)

        self.save_account(self.latest_account)

    def update_account(self, security_id, new_position, timestamp):
        # 先去掉之前的position
        positions = [position for position in self.latest_account.positions if position.security_id != security_id]
        # 更新为新的position
        positions.append(new_position)
        self.latest_account.positions = positions

        self.latest_account.timestamp = to_pd_timestamp(timestamp)

        self.save_account(self.latest_account)

    def update_position(self, current_position, order_amount, current_price, order_type):
        """

        :param current_position:
        :type current_position: Position
        :param order_amount:
        :type order_amount:
        :param current_price:
        :type current_price:
        :param order_type:
        :type order_type:
        """
        if order_type == ORDER_TYPE_LONG:
            need_money = (order_amount * current_price) * (1 + self.slippage + self.buy_cost)
            if self.latest_account.cash < need_money:
                raise NotEnoughMoneyError()

            self.latest_account.cash -= need_money

            # 计算平均价
            long_amount = current_position.long_amount + order_amount
            current_position.average_long_price = (current_position.average_long_price * current_position.long_amount +
                                                   current_price * order_amount) / long_amount

            current_position.long_amount = long_amount

            if current_position.trading_t == 0:
                current_position.available_long += order_amount

        elif order_type == ORDER_TYPE_SHORT:
            need_money = (order_amount * current_price) * (1 + self.slippage + self.buy_cost)
            if self.latest_account.cash < need_money:
                raise NotEnoughMoneyError

            self.latest_account.cash -= need_money

            short_amount = current_position.short_amount + order_amount
            current_position.average_short_price = (current_position.average_short_price * current_position.short_amount
                                                    + current_price * order_amount) / short_amount

            current_position.short_amount = short_amount

            if current_position.trading_t == 0:
                current_position.available_short += order_amount

        elif order_type == ORDER_TYPE_CLOSE_LONG:
            self.latest_account.cash += (order_amount * current_price * (1 - self.slippage - self.sell_cost))

            current_position.available_long -= order_amount
            current_position.long_amount -= order_amount

        elif order_type == ORDER_TYPE_CLOSE_SHORT:
            self.latest_account.cash += 2 * (order_amount * current_position.average_short_price)
            self.latest_account.cash -= order_amount * current_price * (1 + self.slippage + self.sell_cost)

            current_position.available_short -= order_amount
            current_position.short_amount -= order_amount

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
            current_position: Position = self.get_current_position(security_id=security_id)
            the_id = '{}_{}_{}'.format(self.trader_name, security_id,
                                       to_time_str(current_timestamp, TIME_FORMAT_ISO8601))

            if not current_position:
                current_position = Position(id=the_id, trader_name=self.trader_name, timestamp=current_timestamp,
                                            security_id=security_id, long_amount=0, available_long=0,
                                            average_long_price=0, short_amount=0,
                                            available_short=0, average_short_price=0, profit=0, value=0)
            else:
                current_position = Position(id=the_id, trader_name=self.trader_name, timestamp=current_timestamp,
                                            security_id=security_id, long_amount=current_position.long_amount,
                                            available_long=current_position.available_long,
                                            average_long_price=current_position.average_long_price,
                                            short_amount=current_position.short_amount,
                                            available_short=current_position.available_short,
                                            average_short_price=current_position.average_short_price,
                                            profit=current_position.profit, value=current_position.value)

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
                    want_pay = self.latest_account.cash * order_pct
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
                    want_pay = self.latest_account.cash * order_pct

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
                            self.logger.warning("{} available_long:{} order_pct:{} order_amount:{}", security_id,
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
                            self.logger.warning("{} available_long:{} order_pct:{} order_amount:{}", security_id,
                                                current_position.available_long, order_pct, order_amount)
                    else:
                        raise Exception("not enough position")

            self.update_account(security_id, current_position, current_timestamp)
