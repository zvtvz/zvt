# -*- coding: utf-8 -*-
import logging
import time
from typing import List

from xtquant import xtconstant, xtdata
from xtquant.xttrader import XtQuantTrader, XtQuantTraderCallback
from xtquant.xttype import StockAccount, XtPosition

from zvt.broker.qmt.errors import QmtError, PositionOverflowError
from zvt.broker.qmt.qmt_quote import _to_qmt_code
from zvt.common.trading_models import BuyParameter, PositionType, SellParameter
from zvt.trader import AccountService, TradingSignal, OrderType, trading_signal_type_to_order_type
from zvt.utils.time_utils import now_pd_timestamp, to_pd_timestamp

logger = logging.getLogger(__name__)


def _to_qmt_order_type(order_type: OrderType):
    if order_type == OrderType.order_long:
        return xtconstant.STOCK_BUY
    elif order_type == OrderType.order_close_long:
        return xtconstant.STOCK_SELL


class MyXtQuantTraderCallback(XtQuantTraderCallback):
    def on_connected(self):
        logger.info("qmt on_connected")

    def on_smt_appointment_async_response(self, response):
        logger.info(f"qmt on_smt_appointment_async_response: {vars(response)}")

    def on_cancel_order_stock_async_response(self, response):
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
        logger.info(f"qmt on_stock_order: {vars(order)}")

    def on_stock_asset(self, asset):
        """
        资金变动推送
        :param asset: XtAsset对象
        :return:
        """
        logger.info(f"qmt on_stock_asset: {vars(asset)}")

    def on_stock_trade(self, trade):
        """
        成交变动推送
        :param trade: XtTrade对象
        :return:
        """
        logger.info(f"qmt on_stock_trade: {vars(trade)}")

    def on_stock_position(self, position):
        """
        持仓变动推送
        :param position: XtPosition对象
        :return:
        """
        logger.info(f"qmt on_stock_position: {vars(position)}")

    def on_order_error(self, order_error):
        """
        委托失败推送
        :param order_error:XtOrderError 对象
        :return:
        """
        logger.info(f"qmt on_order_error: {vars(order_error)}")

    def on_cancel_error(self, cancel_error):
        """
        撤单失败推送
        :param cancel_error: XtCancelError 对象
        :return:
        """
        logger.info(f"qmt on_cancel_error: {vars(cancel_error)}")

    def on_order_stock_async_response(self, response):
        """
        异步下单回报推送
        :param response: XtOrderResponse 对象
        :return:
        """
        logger.info(f"qmt on_order_stock_async_response: {vars(response)}")

    def on_account_status(self, status):
        """
        :param response: XtAccountStatus 对象
        :return:
        """
        logger.info(status.account_id, status.account_type, status.status)


class QmtStockAccount(AccountService):
    def __init__(self, path, account_id, trader_name, session_id=None) -> None:
        if not session_id:
            session_id = int(time.time())
        self.trader_name = trader_name
        logger.info(f"path: {path}, account: {account_id}, trader_name: {trader_name}, session: {session_id}")

        self.xt_trader = XtQuantTrader(path=path, session=session_id)

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
            logger.error(f"qmt trader 连接失败: {connect_result}")
            raise QmtError(f"qmt trader 连接失败: {connect_result}")
        logger.info("qmt trader 建立交易连接成功！")

        # 对交易回调进行订阅，订阅后可以收到交易主推，返回0表示订阅成功
        subscribe_result = self.xt_trader.subscribe(self.account)

        if subscribe_result != 0:
            logger.error(f"账号订阅失败: {subscribe_result}")
            raise QmtError(f"账号订阅失败: {subscribe_result}")
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

    def sell(self, position_strategy: SellParameter):
        # account_type	int	账号类型，参见数据字典
        # account_id	str	资金账号
        # stock_code	str	证券代码
        # volume	int	持仓数量
        # can_use_volume	int	可用数量
        # open_price	float	开仓价
        # market_value	float	市值
        # frozen_volume	int	冻结数量
        # on_road_volume	int	在途股份
        # yesterday_volume	int	昨夜拥股
        # avg_price	float	成本价
        # direction	int	多空方向，股票不适用；参见数据字典
        stock_codes = [_to_qmt_code(entity_id) for entity_id in position_strategy.entity_ids]
        for i, stock_code in enumerate(stock_codes):
            pct = position_strategy.sell_pcts[i]
            position = self.xt_trader.query_stock_position(self.account, stock_code)
            fix_result_order_id = self.xt_trader.order_stock(
                account=self.account,
                stock_code=stock_code,
                order_type=xtconstant.STOCK_SELL,
                order_volume=int(position.can_use_volume * pct),
                price_type=xtconstant.MARKET_SH_CONVERT_5_CANCEL,
                price=0,
                strategy_name=self.trader_name,
                order_remark="order from zvt",
            )
            logger.info(f"order result id: {fix_result_order_id}")

    def buy(self, buy_parameter: BuyParameter):
        # account_type	int	账号类型，参见数据字典
        # account_id	str	资金账号
        # cash	float	可用金额
        # frozen_cash	float	冻结金额
        # market_value	float	持仓市值
        # total_asset	float	总资产
        acc = self.get_current_account()

        # 优先使用金额下单
        if buy_parameter.money_to_use:
            money_to_use = buy_parameter.money_to_use
            if acc.cash < money_to_use:
                raise QmtError(f"可用余额不足 {acc.cash} < {money_to_use}")
        else:
            # 检查仓位
            if buy_parameter.position_type == PositionType.normal:
                current_pct = round(acc.market_value / acc.total_asset, 2)
                if current_pct >= buy_parameter.position_pct:
                    raise PositionOverflowError(f"目前仓位为{current_pct}, 已超过请求的仓位: {buy_parameter.position_pct}")

                money_to_use = acc.total_asset * (buy_parameter.position_pct - current_pct)
            elif buy_parameter.position_type == PositionType.cash:
                money_to_use = acc.cash * buy_parameter.position_pct
            else:
                assert False

        stock_codes = [_to_qmt_code(entity_id) for entity_id in buy_parameter.entity_ids]
        ticks = xtdata.get_full_tick(code_list=stock_codes)

        if not buy_parameter.weights:
            stocks_count = len(stock_codes)
            money_for_stocks = [round(money_to_use / stocks_count)] * stocks_count
        else:
            weights_sum = sum(buy_parameter.weights)
            money_for_stocks = [round(weight / weights_sum) for weight in buy_parameter.weights]

        for i, stock_code in enumerate(stock_codes):
            try_price = ticks[stock_code]["askPrice"][3]
            volume = money_for_stocks[i] / try_price
            fix_result_order_id = self.xt_trader.order_stock(
                account=self.account,
                stock_code=stock_code,
                order_type=xtconstant.STOCK_BUY,
                order_volume=volume,
                price_type=xtconstant.MARKET_SH_CONVERT_5_CANCEL,
                price=0,
                strategy_name=self.trader_name,
                order_remark="order from zvt",
            )
            logger.info(f"order result id: {fix_result_order_id}")


if __name__ == "__main__":
    account = QmtStockAccount(path=r"D:\qmt\userdata_mini", account_id="")
    account.get_positions()


# the __all__ is generated
__all__ = ["MyXtQuantTraderCallback", "QmtStockAccount"]
