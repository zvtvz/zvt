# -*- coding: utf-8 -*-
import logging
import time
import sys

from typing import List

from xtquant import xtconstant, xtdata
from xtquant.xttrader import XtQuantTrader, XtQuantTraderCallback
from xtquant.xttype import StockAccount, XtPosition

from zvt.broker.qmt import qmt_api
from zvt.broker.qmt.qmt_api import _to_qmt_code
from zvt.trader import AccountService, TradingSignal, OrderType, trading_signal_type_to_order_type
from zvt.utils import now_pd_timestamp, to_pd_timestamp

logger = logging.getLogger(__name__)


def _to_qmt_order_type(order_type: OrderType):
    if order_type == OrderType.order_long:
        return xtconstant.STOCK_BUY
    elif order_type == OrderType.order_close_long:
        return xtconstant.STOCK_SELL


class MyXtQuantTraderCallback(XtQuantTraderCallback):
    def on_connected(self):
        super().on_connected()
        logger.info("qmt on_connected")

    def on_smt_appointment_async_response(self, response):
        super().on_smt_appointment_async_response(response)
        logger.info(f"qmt on_smt_appointment_async_response: {vars(response)}")

    def on_cancel_order_stock_async_response(self, response):
        super().on_cancel_order_stock_async_response(response)
        logger.info(f"qmt on_cancel_order_stock_async_response: {vars(response)}")

    def on_disconnected(self):
        """
        连接断开
        :return:
        """
        logger.info(f"qmt on_disconnected")

    def on_stock_order(self, order):
        """
        委托回报推送
        :param order: XtOrder对象
        :return:
        """
        super().on_stock_order(order)
        logger.info(f"qmt on_stock_order: {vars(order)}")

    def on_stock_asset(self, asset):
        """
        资金变动推送
        :param asset: XtAsset对象
        :return:
        """
        super().on_stock_asset(asset)
        logger.info(f"qmt on_stock_asset: {vars(asset)}")

    def on_stock_trade(self, trade):
        """
        成交变动推送
        :param trade: XtTrade对象
        :return:
        """
        super().on_stock_trade(trade)
        logger.info(f"qmt on_stock_trade: {vars(trade)}")

    def on_stock_position(self, position):
        """
        持仓变动推送
        :param position: XtPosition对象
        :return:
        """
        super().on_stock_position(position)
        logger.info(f"qmt on_stock_position: {vars(position)}")

    def on_order_error(self, order_error):
        """
        委托失败推送
        :param order_error:XtOrderError 对象
        :return:
        """
        super().on_order_error(order_error)
        logger.info(f"qmt on_order_error: {vars(order_error)}")

    def on_cancel_error(self, cancel_error):
        """
        撤单失败推送
        :param cancel_error: XtCancelError 对象
        :return:
        """
        super().on_cancel_error(cancel_error)
        logger.info(f"qmt on_cancel_error: {vars(cancel_error)}")

    def on_order_stock_async_response(self, response):
        """
        异步下单回报推送
        :param response: XtOrderResponse 对象
        :return:
        """
        super().on_order_stock_async_response(response)
        logger.info(f"qmt on_order_stock_async_response: {vars(response)}")

    def on_account_status(self, status):
        """
        :param response: XtAccountStatus 对象
        :return:
        """
        logger.info("on_account_status")
        logger.info(status.account_id, status.account_type, status.status)


class QmtStockAccount(AccountService):
    def __init__(self, path, account_id, trader_name, session_id=None) -> None:
        if not session_id:
            session_id = int(time.time())
        self.trader_name = trader_name
        logger.info(f"path: {path}, account: {account_id}, trader_name: {trader_name}, session: {session_id}")

        self.xt_trader = XtQuantTrader(path, session_id)

        # StockAccount可以用第二个参数指定账号类型，如沪港通传'HUGANGTONG'，深港通传'SHENGANGTONG'
        self.account = StockAccount(account_id=account_id, account_type="STOCK")

        # 创建交易回调类对象，并声明接收回调
        callback = MyXtQuantTraderCallback()
        self.xt_trader.register_callback(callback)

        # 启动交易线程
        self.xt_trader.start()

        # 建立交易连接，返回0表示连接成功
        connect_result = self.xt_trader.connect()
        if connect_result != 0:
            logger.error(f"连接失败: {connect_result}")
            sys.exit(f"连接失败: {connect_result}")
        logger.info("建立交易连接成功！")

        # 对交易回调进行订阅，订阅后可以收到交易主推，返回0表示订阅成功
        subscribe_result = self.xt_trader.subscribe(self.account)
        if subscribe_result != 0:
            logger.error(f"账号订阅失败: {subscribe_result}")
            sys.exit(f"账号订阅失败: {subscribe_result}")
        logger.info("账号订阅成功！")

    def get_positions(self):
        positions: List[XtPosition] = self.xt_trader.query_stock_positions(self.account)
        return positions

    def get_current_position(self, entity_id, create_if_not_exist=False):
        stock_code = _to_qmt_code(entity_id=entity_id)
        # 根据股票代码查询对应持仓
        return self.xt_trader.query_stock_position(self.account, stock_code)

    def get_current_account(self):
        asset = self.xt_trader.query_stock_asset(self.account)
        return asset

    def order_by_amount(self, entity_id, order_price, order_timestamp, order_type, order_amount):
        stock_code = _to_qmt_code(entity_id=entity_id)
        fix_result_order_id = self.xt_trader.order_stock(
            account=self.account,
            stock_code=stock_code,
            order_type=_to_qmt_order_type(order_type=order_type),
            order_volume=order_amount,
            price_type=xtconstant.FIX_PRICE,
            price=order_price,
            strategy_name=self.trader_name,
            order_remark="order from zvt",
        )
        logger.info(f"order result id: {fix_result_order_id}")

    def on_trading_signals(self, trading_signals: List[TradingSignal]):
        for trading_signal in trading_signals:
            try:
                self.handle_trading_signal(trading_signal)
            except Exception as e:
                logger.exception(e)
                self.on_trading_error(timestamp=trading_signal.happen_timestamp, error=e)

    def handle_trading_signal(self, trading_signal: TradingSignal):
        entity_id = trading_signal.entity_id
        happen_timestamp = trading_signal.happen_timestamp
        order_type = trading_signal_type_to_order_type(trading_signal.trading_signal_type)
        trading_level = trading_signal.trading_level.value
        # askPrice	多档委卖价
        # bidPrice	多档委买价
        # askVol	多档委卖量
        # bidVol	多档委买量
        if now_pd_timestamp() > to_pd_timestamp(trading_signal.due_timestamp):
            logger.warning(
                f"the signal is expired, now {now_pd_timestamp()} is after due time: {trading_signal.due_timestamp}"
            )
            return
        quote = xtdata.get_l2_quote(stock_code=_to_qmt_code(entity_id=entity_id), start_time=happen_timestamp)
        if order_type == OrderType.order_long:
            price = quote["askPrice"]
        elif order_type == OrderType.order_close_long:
            price = quote["bidPrice"]
        else:
            assert False
        self.order_by_amount(
            entity_id=entity_id,
            order_price=price,
            order_timestamp=happen_timestamp,
            order_type=order_type,
            order_amount=trading_signal.order_amount,
        )

    def on_trading_open(self, timestamp):
        pass

    def on_trading_close(self, timestamp):
        pass

    def on_trading_finish(self, timestamp):
        pass

    def on_trading_error(self, timestamp, error):
        pass


if __name__ == "__main__":
    account = QmtStockAccount(path=r"D:\qmt\userdata_mini", account_id="")
    account.get_positions()
