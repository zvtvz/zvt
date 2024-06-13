# -*- coding: utf-8 -*-
from zvt.api.kdata import get_kdata
from zvt.contract import IntervalLevel, AdjustType
from zvt.samples import MyBullTrader, StockTrader
from zvt.utils.time_utils import is_same_date

buy_timestamp = "2019-05-29"
sell_timestamp = "2020-01-06"


class SingleTrader(StockTrader):
    def on_time(self, timestamp):
        if is_same_date(buy_timestamp, timestamp):
            self.buy(timestamp=buy_timestamp, entity_ids=["stock_sz_000338"])
        if is_same_date(sell_timestamp, timestamp):
            self.sell(timestamp=sell_timestamp, entity_ids=["stock_sz_000338"])

    def long_position_control(self):
        return 1


def test_single_trader():
    trader = SingleTrader(
        provider="joinquant",
        codes=["000338"],
        level=IntervalLevel.LEVEL_1DAY,
        start_timestamp="2019-01-01",
        end_timestamp="2020-01-10",
        trader_name="000338_single_trader",
        draw_result=True,
    )
    trader.run()

    positions = trader.get_current_account().positions
    print(positions)

    account = trader.get_current_account()

    print(account)

    buy_price = get_kdata(
        provider="joinquant",
        entity_id="stock_sz_000338",
        start_timestamp=buy_timestamp,
        end_timestamp=buy_timestamp,
        return_type="domain",
    )[0]
    sell_price = get_kdata(
        provider="joinquant",
        entity_id="stock_sz_000338",
        start_timestamp=sell_timestamp,
        end_timestamp=sell_timestamp,
        return_type="domain",
    )[0]

    sell_lost = trader.account_service.slippage + trader.account_service.sell_cost
    buy_lost = trader.account_service.slippage + trader.account_service.buy_cost
    pct = (sell_price.close * (1 - sell_lost) - buy_price.close * (1 + buy_lost)) / buy_price.close * (1 + buy_lost)

    profit_rate = (account.all_value - account.input_money) / account.input_money

    assert round(profit_rate, 2) == round(pct, 2)


class MultipleTrader(StockTrader):
    has_buy = False

    def on_time(self, timestamp):
        if is_same_date(buy_timestamp, timestamp):
            self.buy(timestamp=timestamp, entity_ids=["stock_sz_000338"])
            self.has_buy = True
            self.buy(timestamp=timestamp, entity_ids=["stock_sh_601318"])
        if is_same_date(sell_timestamp, timestamp):
            self.sell(
                timestamp=timestamp,
                entity_ids=["stock_sz_000338", "stock_sh_601318"],
            )

    def long_position_control(self):
        if self.has_buy:
            position_pct = 1.0
        else:
            position_pct = 0.5

        return position_pct


def test_multiple_trader():
    trader = MultipleTrader(
        provider="joinquant",
        codes=["000338", "601318"],
        level=IntervalLevel.LEVEL_1DAY,
        start_timestamp="2019-01-01",
        end_timestamp="2020-01-10",
        trader_name="multiple_trader",
        draw_result=False,
        adjust_type=AdjustType.qfq,
    )
    trader.run()

    positions = trader.get_current_account().positions
    print(positions)

    account = trader.get_current_account()

    print(account)

    # 000338
    buy_price = get_kdata(
        provider="joinquant",
        entity_id="stock_sz_000338",
        start_timestamp=buy_timestamp,
        end_timestamp=buy_timestamp,
        return_type="domain",
    )[0]
    sell_price = get_kdata(
        provider="joinquant",
        entity_id="stock_sz_000338",
        start_timestamp=sell_timestamp,
        end_timestamp=sell_timestamp,
        return_type="domain",
    )[0]

    sell_lost = trader.account_service.slippage + trader.account_service.sell_cost
    buy_lost = trader.account_service.slippage + trader.account_service.buy_cost
    pct1 = (sell_price.close * (1 - sell_lost) - buy_price.close * (1 + buy_lost)) / buy_price.close * (1 + buy_lost)

    # 601318
    buy_price = get_kdata(
        provider="joinquant",
        entity_id="stock_sh_601318",
        start_timestamp=buy_timestamp,
        end_timestamp=buy_timestamp,
        return_type="domain",
    )[0]
    sell_price = get_kdata(
        provider="joinquant",
        entity_id="stock_sh_601318",
        start_timestamp=sell_timestamp,
        end_timestamp=sell_timestamp,
        return_type="domain",
    )[0]

    pct2 = (sell_price.close * (1 - sell_lost) - buy_price.close * (1 + buy_lost)) / buy_price.close * (1 + buy_lost)

    profit_rate = (account.all_value - account.input_money) / account.input_money

    assert profit_rate - (pct1 + pct2) / 2 <= 0.2


def test_basic_trader():
    try:
        MyBullTrader(
            provider="joinquant",
            codes=["000338"],
            level=IntervalLevel.LEVEL_1DAY,
            start_timestamp="2018-01-01",
            end_timestamp="2019-06-30",
            trader_name="000338_bull_trader",
            draw_result=False,
        ).run()
    except:
        assert False
