# -*- coding: utf-8 -*-
from zvt.contract import IntervalLevel
from zvt.contract.utils import evaluate_size_from_timestamp, next_timestamp_on_level, is_finished_kdata_timestamp
from zvt.utils.time_utils import (
    to_pd_timestamp,
    split_time_interval,
    is_same_date,
    month_start_end_ranges,
    count_interval,
)


def test_evaluate_size_from_timestamp():
    size = evaluate_size_from_timestamp(
        start_timestamp="2019-01-01",
        end_timestamp="2019-01-02",
        level=IntervalLevel.LEVEL_1MON,
        one_day_trading_minutes=4 * 60,
    )

    assert size == 2

    size = evaluate_size_from_timestamp(
        start_timestamp="2019-01-01",
        end_timestamp="2019-01-02",
        level=IntervalLevel.LEVEL_1WEEK,
        one_day_trading_minutes=4 * 60,
    )

    assert size == 2

    size = evaluate_size_from_timestamp(
        start_timestamp="2019-01-01",
        end_timestamp="2019-01-02",
        level=IntervalLevel.LEVEL_1DAY,
        one_day_trading_minutes=4 * 60,
    )

    assert size == 2

    size = evaluate_size_from_timestamp(
        start_timestamp="2019-01-01",
        end_timestamp="2019-01-02",
        level=IntervalLevel.LEVEL_1HOUR,
        one_day_trading_minutes=4 * 60,
    )

    assert size == 9

    size = evaluate_size_from_timestamp(
        start_timestamp="2019-01-01",
        end_timestamp="2019-01-02",
        level=IntervalLevel.LEVEL_1MIN,
        one_day_trading_minutes=4 * 60,
    )

    assert size == 481


def test_next_timestamp():
    current = "2019-01-10 13:15"
    assert next_timestamp_on_level(current, level=IntervalLevel.LEVEL_1MIN) == to_pd_timestamp("2019-01-10 13:16")
    assert next_timestamp_on_level(current, level=IntervalLevel.LEVEL_5MIN) == to_pd_timestamp("2019-01-10 13:20")
    assert next_timestamp_on_level(current, level=IntervalLevel.LEVEL_15MIN) == to_pd_timestamp("2019-01-10 13:30")


def test_is_finished_kdata_timestamp():
    timestamp = "2019-01-10 13:05"
    assert not is_finished_kdata_timestamp(timestamp, level=IntervalLevel.LEVEL_1DAY)
    assert not is_finished_kdata_timestamp(timestamp, level=IntervalLevel.LEVEL_1HOUR)
    assert not is_finished_kdata_timestamp(timestamp, level=IntervalLevel.LEVEL_30MIN)
    assert not is_finished_kdata_timestamp(timestamp, level=IntervalLevel.LEVEL_15MIN)
    assert is_finished_kdata_timestamp(timestamp, level=IntervalLevel.LEVEL_5MIN)
    assert is_finished_kdata_timestamp(timestamp, level=IntervalLevel.LEVEL_1MIN)

    timestamp = "2019-01-10"
    assert is_finished_kdata_timestamp(timestamp, level=IntervalLevel.LEVEL_1DAY)


def test_split_time_interval():
    first = None
    last = None
    start = "2020-01-01"
    end = "2021-01-01"
    for interval in split_time_interval(start, end, interval=30):
        if first is None:
            first = interval
        last = interval

    print(first)
    print(last)

    assert is_same_date(first[0], start)
    assert is_same_date(first[-1], "2020-01-31")

    assert is_same_date(last[-1], end)


def test_split_time_interval_month():
    first = None
    last = None
    start = "2020-01-01"
    end = "2021-01-01"
    for interval in split_time_interval(start, end, method="month"):
        if first is None:
            first = interval
        last = interval

    print(first)
    print(last)

    assert is_same_date(first[0], start)
    assert is_same_date(first[-1], "2020-01-31")

    assert is_same_date(last[0], "2021-01-01")
    assert is_same_date(last[-1], "2021-01-01")


def test_month_start_end_range():
    start = "2020-01-01"
    end = "2021-01-01"
    ranges = month_start_end_ranges(start_date=start, end_date=end)
    print(ranges)
    assert is_same_date(ranges[0][0], "2020-01-01")
    assert is_same_date(ranges[0][1], "2020-01-31")

    assert is_same_date(ranges[-1][0], "2020-12-01")
    assert is_same_date(ranges[-1][1], "2020-12-31")

    start = "2020-01-01"
    end = "2021-01-31"
    ranges = month_start_end_ranges(start_date=start, end_date=end)
    print(ranges)
    assert is_same_date(ranges[0][0], "2020-01-01")
    assert is_same_date(ranges[0][1], "2020-01-31")

    assert is_same_date(ranges[-1][0], "2021-01-01")
    assert is_same_date(ranges[-1][1], "2021-01-31")


def test_count_interval():
    start = "2020-01-01"
    end = "2021-01-01"
    print(count_interval(start_date=start, end_date=end))
