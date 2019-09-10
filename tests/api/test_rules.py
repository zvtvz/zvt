# -*- coding: utf-8 -*-
from ..context import init_test_context

init_test_context()

from zvdata import IntervalLevel
from zvt.api.rules import coin_finished_timestamp, iterate_timestamps, is_open_time, is_close_time, \
    is_in_finished_timestamps, is_in_trading, is_trading_date
from zvdata.utils.time_utils import is_same_time


def test_is_trading_date():
    assert is_trading_date(entity_type='stock', exchange=None, timestamp='2019-06-28')
    assert not is_trading_date(entity_type='stock', exchange=None, timestamp='2019-06-22')
    assert not is_trading_date(entity_type='stock', exchange=None, timestamp='2019-06-23')


def test_is_open_close_time():
    timestamps = iterate_timestamps(entity_type='coin', exchange='binance',
                                    level=IntervalLevel.LEVEL_1MIN, start_timestamp='2019-05-01',
                                    end_timestamp='2019-05-01')
    assert is_open_time(entity_type='coin', exchange='binance', timestamp=timestamps[0])
    assert is_close_time(entity_type='coin', exchange='binance', timestamp=timestamps[-1])

    timestamps = iterate_timestamps(entity_type='coin', exchange='binance',
                                    level=IntervalLevel.LEVEL_5MIN, start_timestamp='2019-05-01',
                                    end_timestamp='2019-05-01')
    assert is_open_time(entity_type='coin', exchange='binance', timestamp=timestamps[0])
    assert is_close_time(entity_type='coin', exchange='binance', timestamp=timestamps[-1])

    timestamps = iterate_timestamps(entity_type='coin', exchange='binance',
                                    level=IntervalLevel.LEVEL_5MIN, start_timestamp='2019-05-01',
                                    end_timestamp='2019-05-02')
    open = []
    close = []
    for timestamp in timestamps:
        if is_open_time(entity_type='coin', exchange='binance', timestamp=timestamp):
            open.append(timestamp)
        if is_close_time(entity_type='coin', exchange='binance', timestamp=timestamp):
            close.append(timestamp)
    assert len(open) == 3
    assert len(close) == 3


def test_iterate_coin_timestamps():
    timestamps = iterate_timestamps(entity_type='coin', exchange='binance',
                                    level=IntervalLevel.LEVEL_1HOUR, start_timestamp='2019-05-01',
                                    end_timestamp='2019-05-02')
    assert is_same_time(timestamps[0], '2019-05-01 00:00:00')
    assert is_same_time(timestamps[-1], '2019-05-03 00:00:00')

    timestamps = iterate_timestamps(entity_type='coin', exchange='binance',
                                    level=IntervalLevel.LEVEL_5MIN, start_timestamp='2019-05-01',
                                    end_timestamp='2019-05-02')
    assert is_same_time(timestamps[0], '2019-05-01 00:00:00')
    assert is_same_time(timestamps[-1], '2019-05-03 00:00:00')


def test_iterate_stock_timestamps():
    timestamps = iterate_timestamps(entity_type='stock', exchange='sh',
                                    level=IntervalLevel.LEVEL_1HOUR, start_timestamp='2019-05-01',
                                    end_timestamp='2019-05-02')
    assert is_same_time(timestamps[0], '2019-05-01 09:30:00')
    assert is_same_time(timestamps[-1], '2019-05-02 15:00:00')

    timestamps = iterate_timestamps(entity_type='stock', exchange='sh',
                                    level=IntervalLevel.LEVEL_5MIN, start_timestamp='2019-05-01',
                                    end_timestamp='2019-05-02')
    assert is_same_time(timestamps[0], '2019-05-01 09:30:00')
    assert is_same_time(timestamps[-1], '2019-05-02 15:00:00')

    timestamps = iterate_timestamps(entity_type='stock', exchange='sh',
                                    level=IntervalLevel.LEVEL_1HOUR, start_timestamp='2019-05-01',
                                    end_timestamp='2019-05-02', contain_all_timestamp=False)
    assert is_same_time(timestamps[0], '2019-05-01 10:30:00')
    assert is_same_time(timestamps[-1], '2019-05-02 15:00:00')

    timestamps = iterate_timestamps(entity_type='stock', exchange='sh',
                                    level=IntervalLevel.LEVEL_5MIN, start_timestamp='2019-05-01',
                                    end_timestamp='2019-05-02', contain_all_timestamp=False)
    assert is_same_time(timestamps[0], '2019-05-01 09:35:00')
    assert is_same_time(timestamps[-1], '2019-05-02 15:00:00')


def test_coin_finished_timestamp():
    assert coin_finished_timestamp('1999-01-01 00:00:00', level=IntervalLevel.LEVEL_1MIN)
    assert coin_finished_timestamp('1999-01-01 00:00:00', level=IntervalLevel.LEVEL_5MIN)
    assert coin_finished_timestamp('1999-01-01 00:00:00', level=IntervalLevel.LEVEL_15MIN)
    assert coin_finished_timestamp('1999-01-01 00:00:00', level=IntervalLevel.LEVEL_30MIN)
    assert coin_finished_timestamp('1999-01-01 00:00:00', level=IntervalLevel.LEVEL_1HOUR)
    assert coin_finished_timestamp('1999-01-01 00:00:00', level=IntervalLevel.LEVEL_1DAY)

    assert coin_finished_timestamp('1999-01-01 00:01:00', level=IntervalLevel.LEVEL_1MIN)
    assert not coin_finished_timestamp('1999-01-01 00:01:00', level=IntervalLevel.LEVEL_5MIN)
    assert not coin_finished_timestamp('1999-01-01 00:01:00', level=IntervalLevel.LEVEL_15MIN)
    assert not coin_finished_timestamp('1999-01-01 00:01:00', level=IntervalLevel.LEVEL_30MIN)
    assert not coin_finished_timestamp('1999-01-01 00:01:00', level=IntervalLevel.LEVEL_1HOUR)
    assert not coin_finished_timestamp('1999-01-01 00:01:00', level=IntervalLevel.LEVEL_1DAY)

    assert coin_finished_timestamp('1999-01-01 00:05:00', level=IntervalLevel.LEVEL_1MIN)
    assert coin_finished_timestamp('1999-01-01 00:05:00', level=IntervalLevel.LEVEL_5MIN)
    assert not coin_finished_timestamp('1999-01-01 00:05:00', level=IntervalLevel.LEVEL_15MIN)
    assert not coin_finished_timestamp('1999-01-01 00:05:00', level=IntervalLevel.LEVEL_30MIN)
    assert not coin_finished_timestamp('1999-01-01 00:05:00', level=IntervalLevel.LEVEL_1HOUR)
    assert not coin_finished_timestamp('1999-01-01 00:05:00', level=IntervalLevel.LEVEL_1DAY)

    assert coin_finished_timestamp('1999-01-01 00:15:00', level=IntervalLevel.LEVEL_1MIN)
    assert coin_finished_timestamp('1999-01-01 00:15:00', level=IntervalLevel.LEVEL_5MIN)
    assert coin_finished_timestamp('1999-01-01 00:15:00', level=IntervalLevel.LEVEL_15MIN)
    assert not coin_finished_timestamp('1999-01-01 00:15:00', level=IntervalLevel.LEVEL_30MIN)
    assert not coin_finished_timestamp('1999-01-01 00:15:00', level=IntervalLevel.LEVEL_1HOUR)
    assert not coin_finished_timestamp('1999-01-01 00:15:00', level=IntervalLevel.LEVEL_1DAY)

    assert coin_finished_timestamp('1999-01-01 00:30:00', level=IntervalLevel.LEVEL_1MIN)
    assert coin_finished_timestamp('1999-01-01 00:30:00', level=IntervalLevel.LEVEL_5MIN)
    assert coin_finished_timestamp('1999-01-01 00:30:00', level=IntervalLevel.LEVEL_15MIN)
    assert coin_finished_timestamp('1999-01-01 00:30:00', level=IntervalLevel.LEVEL_30MIN)
    assert not coin_finished_timestamp('1999-01-01 00:30:00', level=IntervalLevel.LEVEL_1HOUR)
    assert not coin_finished_timestamp('1999-01-01 00:30:00', level=IntervalLevel.LEVEL_1DAY)

    assert coin_finished_timestamp('1999-01-01 00:45:00', level=IntervalLevel.LEVEL_1MIN)
    assert coin_finished_timestamp('1999-01-01 00:45:00', level=IntervalLevel.LEVEL_5MIN)
    assert coin_finished_timestamp('1999-01-01 00:45:00', level=IntervalLevel.LEVEL_15MIN)
    assert not coin_finished_timestamp('1999-01-01 00:45:00', level=IntervalLevel.LEVEL_30MIN)
    assert not coin_finished_timestamp('1999-01-01 00:45:00', level=IntervalLevel.LEVEL_1HOUR)
    assert not coin_finished_timestamp('1999-01-01 00:45:00', level=IntervalLevel.LEVEL_1DAY)


def test_is_in_finished_timestamps():
    assert is_in_finished_timestamps(entity_type='stock', exchange='sh', timestamp='1999-01-01',
                                     level=IntervalLevel.LEVEL_1DAY)
    assert is_in_finished_timestamps(entity_type='stock', exchange='sh', timestamp='1999-01-01 15:00',
                                     level=IntervalLevel.LEVEL_1DAY)
    assert not is_in_finished_timestamps(entity_type='stock', exchange='sh', timestamp='1999-01-01 14:00',
                                         level=IntervalLevel.LEVEL_1DAY)

    assert is_in_finished_timestamps(entity_type='stock', exchange='sh', timestamp='1999-01-01 09:31',
                                     level=IntervalLevel.LEVEL_1MIN)
    assert not is_in_finished_timestamps(entity_type='stock', exchange='sh', timestamp='1999-01-01 09:30',
                                         level=IntervalLevel.LEVEL_1MIN)

    assert not is_in_finished_timestamps(entity_type='stock', exchange='sh', timestamp='1999-01-01 08:30',
                                         level=IntervalLevel.LEVEL_1MIN)

    assert is_in_finished_timestamps(entity_type='stock', exchange='sh', timestamp='1999-01-01 11:30',
                                     level=IntervalLevel.LEVEL_1MIN)
    assert is_in_finished_timestamps(entity_type='stock', exchange='sh', timestamp='1999-01-01 11:30',
                                     level=IntervalLevel.LEVEL_5MIN)
    assert is_in_finished_timestamps(entity_type='stock', exchange='sh', timestamp='1999-01-01 11:30',
                                     level=IntervalLevel.LEVEL_15MIN)
    assert is_in_finished_timestamps(entity_type='stock', exchange='sh', timestamp='1999-01-01 11:30',
                                     level=IntervalLevel.LEVEL_30MIN)
    assert is_in_finished_timestamps(entity_type='stock', exchange='sh', timestamp='1999-01-01 11:30',
                                     level=IntervalLevel.LEVEL_1HOUR)


def test_is_in_trading():
    assert not is_in_trading(entity_type='stock', exchange='sh', timestamp='2019-06-24')
