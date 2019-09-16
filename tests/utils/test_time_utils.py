# -*- coding: utf-8 -*-
from zvdata import IntervalLevel
from zvdata.utils.time_utils import evaluate_size_from_timestamp, next_timestamp, to_pd_timestamp


def test_evaluate_size_from_timestamp():
    size = evaluate_size_from_timestamp(start_timestamp='2019-01-01', end_timestamp='2019-01-02',
                                        level=IntervalLevel.LEVEL_1MON, one_day_trading_minutes=4 * 60)

    assert size == 2

    size = evaluate_size_from_timestamp(start_timestamp='2019-01-01', end_timestamp='2019-01-02',
                                        level=IntervalLevel.LEVEL_1WEEK, one_day_trading_minutes=4 * 60)

    assert size == 2

    size = evaluate_size_from_timestamp(start_timestamp='2019-01-01', end_timestamp='2019-01-02',
                                        level=IntervalLevel.LEVEL_1DAY, one_day_trading_minutes=4 * 60)

    assert size == 2

    size = evaluate_size_from_timestamp(start_timestamp='2019-01-01', end_timestamp='2019-01-02',
                                        level=IntervalLevel.LEVEL_1HOUR, one_day_trading_minutes=4 * 60)

    assert size == 9

    size = evaluate_size_from_timestamp(start_timestamp='2019-01-01', end_timestamp='2019-01-02',
                                        level=IntervalLevel.LEVEL_1MIN, one_day_trading_minutes=4 * 60)

    assert size == 481


def test_next_timestamp():
    current = '2019-01-10 13:15'
    assert next_timestamp(current, level=IntervalLevel.LEVEL_1MIN) == to_pd_timestamp('2019-01-10 13:16')
    assert next_timestamp(current, level=IntervalLevel.LEVEL_5MIN) == to_pd_timestamp('2019-01-10 13:20')
    assert next_timestamp(current, level=IntervalLevel.LEVEL_15MIN) == to_pd_timestamp('2019-01-10 13:30')
