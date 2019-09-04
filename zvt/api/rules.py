# -*- coding: utf-8 -*-
import logging

import pandas as pd
from zvdata import IntervalLevel
from zvdata.utils.time_utils import to_pd_timestamp

from zvt.api.common import decode_entity_id
from zvdata.utils.time_utils import date_and_time, is_same_time, to_time_str, TIME_FORMAT_MINUTE1, now_pd_timestamp, \
    is_same_date

logger = logging.getLogger(__name__)


# TODO:more precise
def is_trading_date(entity_type, exchange, timestamp: pd.Timestamp):
    if type(timestamp) == str:
        timestamp = to_pd_timestamp(timestamp)

    # just ignore 00:00
    # the_date = date_and_time(timestamp, '09:00')

    if entity_type == 'stock':
        return (timestamp.weekday() != 5) and (timestamp.weekday() != 6)

    return True


# make sure the timestamp is in trading date at first
# this function is used to handle unfinished kdata
def is_in_trading(entity_type, exchange, timestamp):
    current = now_pd_timestamp()
    timestamp = to_pd_timestamp(timestamp)
    if is_same_date(current, timestamp):
        for start, end in get_trading_intervals(entity_type=entity_type, exchange=exchange):
            if current > date_and_time(current, start) and current < date_and_time(current, end):
                return True
    return False


def get_trading_intervals(entity_type, exchange):
    if entity_type == 'stock' and exchange in ('sh', 'sz'):
        return ('09:30', '11:30'), ('13:00', '15:00')

    if entity_type == 'coin':
        return ('00:00', '00:00'),


def generate_finished_timestamps(entity_type, exchange, level):
    return [to_time_str(timestamp, fmt=TIME_FORMAT_MINUTE1) for timestamp in
            iterate_timestamps(entity_type=entity_type, exchange=exchange,
                               start_timestamp='1999-01-01', end_timestamp='1999-01-01', level=level,
                               contain_all_timestamp=False, kdata_use_begin_time=False)]


def iterate_timestamps(entity_type, exchange, start_timestamp: pd.Timestamp, end_timestamp: pd.Timestamp,
                       level=IntervalLevel.LEVEL_1DAY, contain_all_timestamp=True,
                       kdata_use_begin_time=False) -> pd.Timestamp:
    """

    :param entity_type:
    :type entity_type: Union[str, zvt.domain.common.SecurityType]
    :param exchange:
    :type exchange: str
    :param start_timestamp:
    :type start_timestamp: Union[str, pd.Timestamp]
    :param end_timestamp:
    :type end_timestamp: Union[str, pd.Timestamp]
    :param level:
    :type level: zvt.domain.common.IntervalLevel
    :param contain_all_timestamp: always contain begin and end timestamp
    :type contain_all_timestamp: bool
    :param kdata_use_begin_time: true means the interval [timestamp,timestamp+level),false means [timestamp-level,timestamp)
    :type kdata_use_begin_time: bool
    :return:
    :rtype: List[pandas._libs.tslibs.timestamps.Timestamp]
    """
    date_range = pd.date_range(start=start_timestamp, end=end_timestamp,
                               freq='1D').tolist()

    if level == IntervalLevel.LEVEL_1DAY:
        return date_range

    if level < IntervalLevel.LEVEL_1DAY:
        start_end_list = get_trading_intervals(entity_type=entity_type, exchange=exchange)

        time_ranges = []

        for date in date_range:
            for start_end in start_end_list:
                start = start_end[0]
                end = start_end[1]

                start_date = date_and_time(the_date=date, the_time=start)
                end_date = date_and_time(the_date=date, the_time=end)

                if end == '00:00':
                    end_date = end_date + pd.Timedelta(days=1)

                time_range = pd.date_range(start=start_date,
                                           end=end_date,
                                           freq=level.to_pd_freq()).tolist()
                if contain_all_timestamp:
                    time_ranges += time_range
                else:
                    if kdata_use_begin_time:
                        time_ranges += time_range[:-1]
                    else:
                        time_ranges += time_range[1:]
        time_ranges = list(set(time_ranges))
        time_ranges.sort()
        return time_ranges

    return date_range


def is_open_time(entity_type, exchange, timestamp):
    return is_same_time(timestamp, date_and_time(the_date=timestamp,
                                                 the_time=get_trading_intervals(entity_type=entity_type,
                                                                                exchange=exchange)[0][0]))


def is_close_time(entity_type, exchange, timestamp):
    return is_same_time(timestamp, date_and_time(the_date=timestamp,
                                                 the_time=get_trading_intervals(entity_type=entity_type,
                                                                                exchange=exchange)[-1][-1]))


china_stock_level_map_finished_timestamps = {
    IntervalLevel.LEVEL_1DAY.value: ['00:00', '15:00']
}

for level in IntervalLevel:
    if level < IntervalLevel.LEVEL_1DAY:
        china_stock_level_map_finished_timestamps[level.value] = generate_finished_timestamps(
            entity_type='stock', exchange='sh', level=level)


def coin_finished_timestamp(timestamp: pd.Timestamp, level: IntervalLevel):
    timestamp = to_pd_timestamp(timestamp)

    if timestamp.microsecond != 0:
        return False

    return timestamp.minute % level.to_minute() == 0


def china_stock_finished_timestamp(timestamp: pd.Timestamp, level: IntervalLevel):
    timestamp = to_pd_timestamp(timestamp)

    if timestamp.microsecond != 0:
        return False

    return to_time_str(timestamp, fmt=TIME_FORMAT_MINUTE1) in china_stock_level_map_finished_timestamps.get(
        level.value)


def is_in_finished_timestamps(entity_type, exchange, timestamp, level: IntervalLevel):
    """

    :param entity_type:
    :type entity_type: zvt.domain.common.EntityType
    :param exchange:
    :type exchange: str
    :param timestamp: the timestamp could be recorded in kdata of the level
    :type timestamp: pd.Timestamp
    :param level:
    :type level: zvt.domain.common.IntervalLevel
    :return:
    :rtype: bool
    """
    if entity_type == 'stock' and exchange in ('sh', 'sz'):
        return china_stock_finished_timestamp(timestamp, level=level)
    if entity_type == 'coin':
        return coin_finished_timestamp(timestamp, level=level)

    return False


def get_trading_meta(entity_id=None, entity_type=None, exchange=None):
    if entity_id:
        entity_type, exchange, _ = decode_entity_id(entity_id)

    if entity_type == 'future':
        return {
            'trading_t': 0,
            'could_short': True
        }

    if entity_type == 'coin':
        return {
            'trading_t': 0,
            'could_short': True
        }
    if entity_type == 'stock':
        return {
            'trading_t': 1,
            'could_short': False
        }


if __name__ == '__main__':
    # print(is_in_finished_timestamps(entity_type='stock', exchange='sh', level=IntervalLevel.LEVEL_1HOUR,
    #                                 timestamp='1999-01-01 15:00'))
    print(generate_finished_timestamps(entity_type='stock', exchange='sh', level=IntervalLevel.LEVEL_1DAY))
    print(generate_finished_timestamps(entity_type='stock', exchange='sh', level=IntervalLevel.LEVEL_1HOUR))
    # print(is_open_time(entity_type='stock', exchange='sh', timestamp='2018-01-01 09:30:00'))
    #
    for timestamp in iterate_timestamps(entity_type='stock', exchange='sh', start_timestamp='2019-01-01',
                                        end_timestamp='2019-01-05'):
        print(timestamp)

    print('..........')

    for timestamp in iterate_timestamps(entity_type='stock', exchange='sh', start_timestamp='2019-01-01',
                                        end_timestamp='2019-01-05',
                                        level=IntervalLevel.LEVEL_1HOUR):
        print(timestamp)

    print('..........')

    for timestamp in iterate_timestamps(entity_type='stock', exchange='sh', start_timestamp='2019-01-01',
                                        end_timestamp='2019-01-05',
                                        level=IntervalLevel.LEVEL_1HOUR, contain_all_timestamp=True):
        print(timestamp)
