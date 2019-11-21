# -*- coding: utf-8 -*-

import logging
import math

from zvdata.contract import get_db_session
from zvdata import IntervalLevel
from zvt.api.business import get_account
from zvt.api.common import decode_entity_id, get_kdata_schema
from zvt.api.rules import get_trading_meta
from zvt.api.quote import get_kdata
from zvt.domain import Order
from zvt.domain.business import SimAccount, Position
from zvt.trader import TradingSignalType, TradingListener, TradingSignal
from zvt.trader.errors import NotEnoughMoneyError, InvalidOrderError, NotEnoughPositionError, InvalidOrderParamError
from zvdata.utils.time_utils import to_pd_timestamp, to_time_str, TIME_FORMAT_ISO8601, is_same_date
from zvdata.utils.utils import fill_domain_from_dict

ORDER_TYPE_LONG = 'order_long'
ORDER_TYPE_SHORT = 'order_short'
ORDER_TYPE_CLOSE_LONG = 'order_close_long'
ORDER_TYPE_CLOSE_SHORT = 'order_close_short'

from marshmallow_sqlalchemy import ModelSchema


class SimAccountSchema(ModelSchema):
    class Meta:
        model = SimAccount


class PositionSchema(ModelSchema):
    class Meta:
        model = Position


sim_account_schema = SimAccountSchema()
position_schema = PositionSchema()


class AccountService(TradingListener):
    logger = logging.getLogger(__name__)
    trader_name = None

    def get_current_position(self, entity_id):
        pass

    def order(self, entity_id, current_price, current_timestamp, order_amount=0, order_pct=1.0, order_price=0,
              order_type=ORDER_TYPE_LONG, order_money=0):
        pass

    # 开多,对于某些品种只能开多，比如中国股票
    def buy(self, entity_id, current_price, current_timestamp, order_amount=0, order_pct=1.0, order_price=0,
            order_money=0):
        self.order(entity_id, current_price, current_timestamp, order_amount, order_pct, order_price,
                   order_type=ORDER_TYPE_LONG, order_money=order_money)

    # 开空
    def sell(self, entity_id, current_price, current_timestamp, order_amount=0, order_pct=1.0, order_price=0,
             order_money=0):
        self.order(entity_id, current_price, current_timestamp, order_amount, order_pct, order_price,
                   order_type=ORDER_TYPE_SHORT, order_money=order_money)

    # 平多
    def close_long(self, entity_id, current_price, current_timestamp, order_amount=0, order_pct=1.0, order_price=0,
                   order_money=0):
        self.order(entity_id, current_price, current_timestamp, order_amount, order_pct, order_price,
                   order_type=ORDER_TYPE_CLOSE_LONG, order_money=order_money)

    # 平空
    def close_short(self, entity_id, current_price, current_timestamp, order_amount=0, order_pct=1.0, order_price=0,
                    order_money=0):
        self.order(entity_id, current_price, current_timestamp, order_amount, order_pct, order_price,
                   order_type=ORDER_TYPE_CLOSE_SHORT, order_money=order_money)

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
        self.logger.debug('trader:{} received trading signal:{}'.format(self.trader_name, trading_signal))
        entity_id = trading_signal.entity_id
        current_timestamp = trading_signal.the_timestamp
        order_type = AccountService.trading_signal_to_order_type(trading_signal.trading_signal_type)
        trading_level = trading_signal.trading_level.value
        if order_type:
            try:
                kdata = get_kdata(provider=self.provider, entity_id=entity_id, level=trading_level,
                                  start_timestamp=current_timestamp, end_timestamp=current_timestamp,
                                  limit=1)
                if kdata is not None and not kdata.empty:
                    entity_type, _, _ = decode_entity_id(kdata['entity_id'][0])

                    the_price = kdata['close'][0]

                    if the_price:
                        self.order(entity_id=entity_id, current_price=the_price,
                                   current_timestamp=current_timestamp, order_pct=trading_signal.position_pct,
                                   order_money=trading_signal.order_money,
                                   order_type=order_type)
                    else:
                        self.logger.warning(
                            'ignore trading signal,wrong kdata,entity_id:{},timestamp:{},kdata:{}'.format(entity_id,
                                                                                                          current_timestamp,
                                                                                                          kdata.to_dict(
                                                                                                              orient='records')))

                else:
                    self.logger.warning(
                        'ignore trading signal,could not get kdata,entity_id:{},timestamp:{}'.format(entity_id,
                                                                                                     current_timestamp))
            except Exception as e:
                self.logger.exception(e)


class SimAccountService(AccountService):

    def __init__(self, trader_name,
                 timestamp,
                 provider='joinquant',
                 level=IntervalLevel.LEVEL_1DAY,
                 base_capital=1000000,
                 buy_cost=0.001,
                 sell_cost=0.001,
                 slippage=0.001):

        self.base_capital = base_capital
        self.buy_cost = buy_cost
        self.sell_cost = sell_cost
        self.slippage = slippage
        self.trader_name = trader_name

        self.session = get_db_session('zvt', 'business')
        self.provider = provider
        self.level = level
        self.start_timestamp = timestamp

        account = get_account(session=self.session, trader_name=self.trader_name, return_type='domain', limit=1)

        if account:
            self.logger.warning("trader:{} has run before,old result would be deleted".format(trader_name))
            self.session.query(SimAccount).filter(SimAccount.trader_name == self.trader_name).delete()
            self.session.query(Position).filter(Position.trader_name == self.trader_name).delete()
            self.session.query(Order).filter(Order.trader_name == self.trader_name).delete()
            self.session.commit()

        account = SimAccount(trader_name=self.trader_name, cash=self.base_capital,
                             positions=[], all_value=self.base_capital, value=0, closing=False,
                             timestamp=timestamp)
        self.latest_account = sim_account_schema.dump(account)

        # self.persist_account(timestamp)

    def on_trading_open(self, timestamp):
        self.logger.info('on_trading_open:{}'.format(timestamp))
        if is_same_date(timestamp, self.start_timestamp):
            return
        # get the account for trading at the date
        accounts = get_account(session=self.session, trader_name=self.trader_name, return_type='domain',
                               end_timestamp=to_time_str(timestamp), limit=1, order=SimAccount.timestamp.desc())
        if accounts:
            account = accounts[0]
        else:
            return

        positions = []
        # FIXME:dump all directly
        for position_domain in account.positions:
            position_dict = position_schema.dump(position_domain)
            self.logger.info('current position:{}'.format(position_dict))
            del position_dict['sim_account']
            positions.append(position_dict)

        self.latest_account = sim_account_schema.dump(account)
        self.latest_account['positions'] = positions
        self.logger.info('on_trading_open:{},latest_account:{}'.format(timestamp, self.latest_account))

    def on_trading_close(self, timestamp):
        self.logger.info('on_trading_close:{}'.format(timestamp))

        self.latest_account['value'] = 0
        self.latest_account['all_value'] = 0
        for position in self.latest_account['positions']:
            entity_type, _, _ = decode_entity_id(position['entity_id'])
            data_schema = get_kdata_schema(entity_type, level=self.level)

            kdata = get_kdata(provider=self.provider, level=self.level, entity_id=position['entity_id'],
                              order=data_schema.timestamp.desc(),
                              end_timestamp=timestamp, limit=1)

            closing_price = kdata['close'][0]

            position['available_long'] = position['long_amount']
            position['available_short'] = position['short_amount']

            if closing_price:
                if (position['long_amount'] is not None) and position['long_amount'] > 0:
                    position['value'] = position['long_amount'] * closing_price
                    self.latest_account['value'] += position['value']
                elif (position['short_amount'] is not None) and position['short_amount'] > 0:
                    position['value'] = 2 * (position['short_amount'] * position['average_short_price'])
                    position['value'] -= position['short_amount'] * closing_price
                    self.latest_account['value'] += position['value']
            else:
                self.logger.warning(
                    'could not refresh close value for position:{},timestamp:{}'.format(position['entity_id'],
                                                                                        timestamp))

        # remove the empty position
        self.latest_account['positions'] = [position for position in self.latest_account['positions'] if
                                            position['long_amount'] > 0 or position['short_amount'] > 0]

        self.latest_account['all_value'] = self.latest_account['value'] + self.latest_account['cash']
        self.latest_account['closing'] = True
        self.latest_account['timestamp'] = to_pd_timestamp(timestamp)

        self.logger.info('on_trading_close:{},latest_account:{}'.format(timestamp, self.latest_account))
        self.persist_account(timestamp)

    def persist_account(self, timestamp):
        """
        save the account to db,we do this after closing time every day

        :param timestamp:
        :type timestamp:
        """
        the_id = '{}_{}'.format(self.trader_name, to_time_str(timestamp, TIME_FORMAT_ISO8601))
        positions = []
        for position in self.latest_account['positions']:
            position_domain = Position()
            fill_domain_from_dict(position_domain, position, None)

            position_domain.id = '{}_{}_{}'.format(self.trader_name, position['entity_id'],
                                                   to_time_str(timestamp, TIME_FORMAT_ISO8601))
            position_domain.timestamp = to_pd_timestamp(timestamp)
            position_domain.sim_account_id = the_id

            positions.append(position_domain)

        account_domain = SimAccount(id=the_id, trader_name=self.trader_name, cash=self.latest_account['cash'],
                                    positions=positions,
                                    all_value=self.latest_account['all_value'], value=self.latest_account['value'],
                                    timestamp=to_pd_timestamp(self.latest_account['timestamp']))

        self.logger.info('persist_account:{}'.format(sim_account_schema.dump(account_domain)))

        self.session.add(account_domain)
        self.session.commit()

    def get_current_position(self, entity_id):
        """
        get current position to design whether order could make

        :param entity_id:
        :type entity_id: str
        :return:
        :rtype: None
        """
        for position in self.latest_account['positions']:
            if position['entity_id'] == entity_id:
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

    def update_position(self, current_position, order_amount, current_price, order_type, timestamp):
        """

        :param timestamp:
        :type timestamp:
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
            if self.latest_account['cash'] < need_money:
                raise NotEnoughMoneyError()

            self.latest_account['cash'] -= need_money

            # 计算平均价
            long_amount = current_position['long_amount'] + order_amount
            current_position['average_long_price'] = (current_position['average_long_price'] * current_position[
                'long_amount'] + current_price * order_amount) / long_amount

            current_position['long_amount'] = long_amount

            if current_position['trading_t'] == 0:
                current_position['available_long'] += order_amount

        elif order_type == ORDER_TYPE_SHORT:
            need_money = (order_amount * current_price) * (1 + self.slippage + self.buy_cost)
            if self.latest_account['cash'] < need_money:
                raise NotEnoughMoneyError

            self.latest_account['cash'] -= need_money

            short_amount = current_position['short_amount'] + order_amount
            current_position['average_short_price'] = (current_position['average_short_price'] * current_position[
                'short_amount']
                                                       + current_price * order_amount) / short_amount

            current_position['short_amount'] = short_amount

            if current_position['trading_t'] == 0:
                current_position['available_short'] += order_amount

        elif order_type == ORDER_TYPE_CLOSE_LONG:
            self.latest_account['cash'] += (order_amount * current_price * (1 - self.slippage - self.sell_cost))

            current_position['available_long'] -= order_amount
            current_position['long_amount'] -= order_amount

        elif order_type == ORDER_TYPE_CLOSE_SHORT:
            self.latest_account['cash'] += 2 * (order_amount * current_position['average_short_price'])
            self.latest_account['cash'] -= order_amount * current_price * (1 + self.slippage + self.sell_cost)

            current_position['available_short'] -= order_amount
            current_position['short_amount'] -= order_amount

        # save the order info to db
        order_id = '{}_{}_{}_{}'.format(self.trader_name, order_type, current_position['entity_id'],
                                        to_time_str(timestamp, TIME_FORMAT_ISO8601))
        order = Order(id=order_id, timestamp=to_pd_timestamp(timestamp), trader_name=self.trader_name,
                      entity_id=current_position['entity_id'], order_price=current_price, order_amount=order_amount,
                      order_type=order_type,
                      status='success')
        self.session.add(order)
        self.session.commit()

    def order(self, entity_id, current_price, current_timestamp, order_amount=0, order_pct=1.0, order_price=0,
              order_type=ORDER_TYPE_LONG, order_money=0):
        """
        下单

        Parameters
        ----------
        entity_id : str
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

        """

        # 市价交易,就是买卖是"当时"并"一定"能成交的
        # 简单起见，目前只支持这种方式
        if order_price == 0:
            current_position = self.get_current_position(entity_id=entity_id)

            if not current_position:
                trading_t = get_trading_meta(entity_id=entity_id)['trading_t']
                current_position = {
                    'trader_name': self.trader_name,
                    'entity_id': entity_id,
                    'long_amount': 0,
                    'available_long': 0,
                    'average_long_price': 0,
                    'short_amount': 0,
                    'available_short': 0,
                    'average_short_price': 0,
                    'profit': 0,
                    'value': 0,
                    'trading_t': trading_t
                }
                # add it to latest account
                self.latest_account['positions'].append(current_position)

            # 按钱交易
            if order_money > 0:
                # 开多
                if order_type == ORDER_TYPE_LONG:
                    if current_position['short_amount'] > 0:
                        raise InvalidOrderError("close the short position before open long")

                    if order_money > self.latest_account['cash']:
                        raise NotEnoughMoneyError()

                    cost = current_price * (1 + self.slippage + self.buy_cost)
                    # 买的数量
                    order_amount = order_money // cost

                    if order_amount > 0:
                        self.update_position(current_position, order_amount, current_price, order_type,
                                             current_timestamp)
                    else:
                        raise NotEnoughMoneyError()
                # 开空
                elif order_type == ORDER_TYPE_SHORT:
                    if current_position['long_amount'] > 0:
                        raise InvalidOrderError("close the long position before open short")

                    if order_money > self.latest_account['cash']:
                        raise NotEnoughMoneyError()

                    cost = current_price * (1 + self.slippage + self.buy_cost)

                    order_amount = order_money // cost
                    if order_amount > 0:
                        self.update_position(current_position, order_amount, current_price, order_type,
                                             current_timestamp)
                    else:
                        raise NotEnoughMoneyError()
                else:
                    raise InvalidOrderParamError('close long/short not support order_money')

            # 按数量交易
            elif order_amount > 0:
                # 开多
                if order_type == ORDER_TYPE_LONG:
                    if current_position['short_amount'] > 0:
                        raise InvalidOrderError("close the short position before open long")

                    self.update_position(current_position, order_amount, current_price, order_type, current_timestamp)
                # 开空
                elif order_type == ORDER_TYPE_SHORT:
                    if current_position['long_amount'] > 0:
                        raise InvalidOrderError("close the long position before open short")

                    self.update_position(current_position, order_amount, current_price, order_type, current_timestamp)
                # 平多
                elif order_type == ORDER_TYPE_CLOSE_LONG:
                    if current_position['available_long'] >= order_amount:
                        self.update_position(current_position, order_amount, current_price, order_type,
                                             current_timestamp)
                    else:
                        raise NotEnoughPositionError()
                # 平空
                elif order_type == ORDER_TYPE_CLOSE_SHORT:
                    if current_position['available_short'] >= order_amount:
                        self.update_position(current_position, order_amount, current_price, order_type,
                                             current_timestamp)
                    else:
                        raise Exception("not enough position")

            # 按仓位比例交易
            elif 0 < order_pct <= 1:
                # 开多
                if order_type == ORDER_TYPE_LONG:
                    if current_position['short_amount'] > 0:
                        raise InvalidOrderError("close the short position before open long")

                    cost = current_price * (1 + self.slippage + self.buy_cost)
                    want_pay = self.latest_account['cash'] * order_pct
                    # 买的数量
                    order_amount = want_pay // cost
                    if order_amount > 0:
                        self.update_position(current_position, order_amount, current_price, order_type,
                                             current_timestamp)
                    else:
                        raise NotEnoughMoneyError()
                # 开空
                elif order_type == ORDER_TYPE_SHORT:
                    if current_position['long_amount'] > 0:
                        raise InvalidOrderError("close the long position before open short")

                    cost = current_price * (1 + self.slippage + self.buy_cost)
                    want_pay = self.latest_account['cash'] * order_pct

                    order_amount = want_pay // cost
                    if order_amount > 0:
                        self.update_position(current_position, order_amount, current_price, order_type,
                                             current_timestamp)
                    else:
                        raise NotEnoughMoneyError()

                # 平多
                elif order_type == ORDER_TYPE_CLOSE_LONG:
                    if current_position['available_long'] > 0:
                        if order_pct == 1.0:
                            order_amount = current_position['available_long']
                        else:
                            order_amount = math.floor(current_position['available_long'] * order_pct)

                        if order_amount != 0:
                            self.update_position(current_position, order_amount, current_price, order_type,
                                                 current_timestamp)
                        else:
                            self.logger.warning("{} available_long:{} order_pct:{} order_amount:{}", entity_id,
                                                current_position['available_long'], order_pct, order_amount)
                    else:
                        raise NotEnoughPositionError()
                # 平空
                elif order_type == ORDER_TYPE_CLOSE_SHORT:
                    if current_position['available_short'] > 0:
                        if order_pct == 1.0:
                            order_amount = current_position['available_short']
                        else:
                            order_amount = math.floor(current_position['available_short'] * order_pct)

                        if order_amount != 0:
                            self.update_position(current_position, order_amount, current_price, order_type,
                                                 current_timestamp)
                        else:
                            self.logger.warning("{} available_long:{} order_pct:{} order_amount:{}", entity_id,
                                                current_position['available_long'], order_pct, order_amount)
                    else:
                        raise Exception("not enough position")
