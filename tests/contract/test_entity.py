# -*- coding: utf-8 -*-
from zvt.contract import EntityMixin, IntervalLevel
from zvt.utils.time_utils import to_pd_timestamp


def test_get_1min_timestamps():
    timestamps = []
    for timestamp in EntityMixin.get_interval_timestamps(start_date='2020-06-17', end_date='2020-06-18',
                                                         level=IntervalLevel.LEVEL_1MIN):
        timestamps.append(timestamp)

    assert to_pd_timestamp('2020-06-17 09:31:00') in timestamps
    assert to_pd_timestamp('2020-06-17 11:30:00') in timestamps
    assert to_pd_timestamp('2020-06-17 13:01:00') in timestamps
    assert to_pd_timestamp('2020-06-17 15:00:00') in timestamps

    assert to_pd_timestamp('2020-06-17 09:31:00') in timestamps
    assert to_pd_timestamp('2020-06-17 11:30:00') in timestamps
    assert to_pd_timestamp('2020-06-17 13:01:00') in timestamps
    assert to_pd_timestamp('2020-06-18 15:00:00') in timestamps


def test_get_1h_timestamps():
    timestamps = []
    for timestamp in EntityMixin.get_interval_timestamps(start_date='2020-06-17', end_date='2020-06-18',
                                                         level=IntervalLevel.LEVEL_1HOUR):
        timestamps.append(timestamp)

    assert to_pd_timestamp('2020-06-17 10:30:00') in timestamps
    assert to_pd_timestamp('2020-06-17 11:30:00') in timestamps
    assert to_pd_timestamp('2020-06-17 14:00:00') in timestamps
    assert to_pd_timestamp('2020-06-17 15:00:00') in timestamps

    assert to_pd_timestamp('2020-06-17 10:30:00') in timestamps
    assert to_pd_timestamp('2020-06-17 11:30:00') in timestamps
    assert to_pd_timestamp('2020-06-17 14:00:00') in timestamps
    assert to_pd_timestamp('2020-06-18 15:00:00') in timestamps


def test_is_finished_kdata_timestamp():
    assert EntityMixin.is_finished_kdata_timestamp('2020-06-17 10:30', IntervalLevel.LEVEL_30MIN)
    assert not EntityMixin.is_finished_kdata_timestamp('2020-06-17 10:30', IntervalLevel.LEVEL_1DAY)

    assert EntityMixin.is_finished_kdata_timestamp('2020-06-17 11:30', IntervalLevel.LEVEL_30MIN)
    assert not EntityMixin.is_finished_kdata_timestamp('2020-06-17 11:30', IntervalLevel.LEVEL_1DAY)

    assert EntityMixin.is_finished_kdata_timestamp('2020-06-17 13:30', IntervalLevel.LEVEL_30MIN)
    assert not EntityMixin.is_finished_kdata_timestamp('2020-06-17 13:30', IntervalLevel.LEVEL_1DAY)


def test_open_close():
    assert EntityMixin.is_open_timestamp('2020-06-17 09:30')
    assert EntityMixin.is_close_timestamp('2020-06-17 15:00')

    timestamps = []
    for timestamp in EntityMixin.get_interval_timestamps(start_date='2020-06-17', end_date='2020-06-18',
                                                         level=IntervalLevel.LEVEL_1HOUR):
        timestamps.append(timestamp)

    assert EntityMixin.is_open_timestamp(timestamps[0])
    assert EntityMixin.is_close_timestamp(timestamps[-1])
