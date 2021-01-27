# -*- coding: utf-8 -*-
import datetime
import math

import arrow
import pandas as pd
import tzlocal

from zvt.contract import IntervalLevel

CHINA_TZ = 'Asia/Shanghai'

TIME_FORMAT_ISO8601 = "YYYY-MM-DDTHH:mm:ss.SSS"

TIME_FORMAT_DAY = 'YYYY-MM-DD'

TIME_FORMAT_DAY1 = 'YYYYMMDD'

TIME_FORMAT_MINUTE = 'YYYYMMDDHHmm'

TIME_FORMAT_MINUTE1 = 'HH:mm'

TIME_FORMAT_MINUTE2 = "YYYY-MM-DD HH:mm:ss"


# ms(int) or second(float) or str
def to_pd_timestamp(the_time) -> pd.Timestamp:
    if the_time is None:
        return None
    if type(the_time) == int:
        return pd.Timestamp.fromtimestamp(the_time / 1000)

    if type(the_time) == float:
        return pd.Timestamp.fromtimestamp(the_time)

    return pd.Timestamp(the_time)


def to_timestamp(the_time):
    return int(to_pd_timestamp(the_time).tz_localize(tzlocal.get_localzone()).timestamp() * 1000)


def now_timestamp():
    return int(pd.Timestamp.utcnow().timestamp() * 1000)


def now_pd_timestamp() -> pd.Timestamp:
    return pd.Timestamp.now()


def to_time_str(the_time, fmt=TIME_FORMAT_DAY):
    try:
        return arrow.get(to_pd_timestamp(the_time)).format(fmt)
    except Exception as e:
        return the_time


def now_time_str(fmt=TIME_FORMAT_DAY):
    return to_time_str(the_time=now_pd_timestamp(), fmt=fmt)


def next_date(the_time, days=1):
    return to_pd_timestamp(the_time) + datetime.timedelta(days=days)


def is_same_date(one, two):
    return to_pd_timestamp(one).date() == to_pd_timestamp(two).date()


def is_same_time(one, two):
    return to_timestamp(one) == to_timestamp(two)


def get_year_quarter(time):
    time = to_pd_timestamp(time)
    return time.year, ((time.month - 1) // 3) + 1


def day_offset_today(offset=0):
    return now_pd_timestamp() + datetime.timedelta(days=offset)


def get_year_quarters(start, end=pd.Timestamp.now()):
    start_year_quarter = get_year_quarter(start)
    current_year_quarter = get_year_quarter(end)
    if current_year_quarter[0] == start_year_quarter[0]:
        return [(current_year_quarter[0], x) for x in range(start_year_quarter[1], current_year_quarter[1] + 1)]
    elif current_year_quarter[0] - start_year_quarter[0] == 1:
        return [(start_year_quarter[0], x) for x in range(start_year_quarter[1], 5)] + \
               [(current_year_quarter[0], x) for x in range(1, current_year_quarter[1] + 1)]
    elif current_year_quarter[0] - start_year_quarter[0] > 1:
        return [(start_year_quarter[0], x) for x in range(start_year_quarter[1], 5)] + \
               [(x, y) for x in range(start_year_quarter[0] + 1, current_year_quarter[0]) for y in range(1, 5)] + \
               [(current_year_quarter[0], x) for x in range(1, current_year_quarter[1] + 1)]
    else:
        raise Exception("wrong start time:{}".format(start))


def date_and_time(the_date, the_time):
    time_str = '{}T{}:00.000'.format(to_time_str(the_date), the_time)

    return to_pd_timestamp(time_str)


def next_timestamp(current_timestamp: pd.Timestamp, level: IntervalLevel) -> pd.Timestamp:
    current_timestamp = to_pd_timestamp(current_timestamp)
    return current_timestamp + pd.Timedelta(seconds=level.to_second())


def evaluate_size_from_timestamp(start_timestamp,
                                 level: IntervalLevel,
                                 one_day_trading_minutes,
                                 end_timestamp: pd.Timestamp = None):
    """
    given from timestamp,level,one_day_trading_minutes,this func evaluate size of kdata to current.
    it maybe a little bigger than the real size for fetching all the kdata.

    :param start_timestamp:
    :type start_timestamp: pd.Timestamp
    :param level:
    :type level: IntervalLevel
    :param one_day_trading_minutes:
    :type one_day_trading_minutes: int
    """
    if not end_timestamp:
        end_timestamp = pd.Timestamp.now()
    else:
        end_timestamp = to_pd_timestamp(end_timestamp)

    time_delta = end_timestamp - to_pd_timestamp(start_timestamp)

    one_day_trading_seconds = one_day_trading_minutes * 60

    if level == IntervalLevel.LEVEL_1DAY:
        return time_delta.days + 1

    if level == IntervalLevel.LEVEL_1WEEK:
        return int(math.ceil(time_delta.days / 7)) + 1

    if level == IntervalLevel.LEVEL_1MON:
        return int(math.ceil(time_delta.days / 30)) + 1

    if time_delta.days > 0:
        seconds = (time_delta.days + 1) * one_day_trading_seconds
        return int(math.ceil(seconds / level.to_second())) + 1
    else:
        seconds = time_delta.total_seconds()
        return min(int(math.ceil(seconds / level.to_second())) + 1,
                   one_day_trading_seconds / level.to_second() + 1)


def is_finished_kdata_timestamp(timestamp, level: IntervalLevel):
    timestamp = to_pd_timestamp(timestamp)
    if level.floor_timestamp(timestamp) == timestamp:
        return True
    return False


def is_in_same_interval(t1: pd.Timestamp, t2: pd.Timestamp, level: IntervalLevel):
    t1 = to_pd_timestamp(t1)
    t2 = to_pd_timestamp(t2)
    if level == IntervalLevel.LEVEL_1WEEK:
        return t1.week == t2.week
    if level == IntervalLevel.LEVEL_1MON:
        return t1.month == t2.month

    return level.floor_timestamp(t1) == level.floor_timestamp(t2)


def split_time_interval(start, end, method=None, interval=30, freq='D'):
    start = to_pd_timestamp(start)
    end = to_pd_timestamp(end)
    if not method:
        while start < end:
            interval_end = min(next_date(start, interval), end)
            yield pd.date_range(start=start, end=interval_end, freq=freq)
            start = next_date(interval_end, 1)

    if method == 'month':
        while start <= end:
            import calendar
            _, day = calendar.monthrange(start.year, start.month)

            interval_end = min(to_pd_timestamp(f'{start.year}-{start.month}-{day}'), end)
            yield pd.date_range(start=start, end=interval_end, freq=freq)
            start = next_date(interval_end, 1)


if __name__ == '__main__':
    print(date_and_time('2019-10-01', '10:00'))
# the __all__ is generated
__all__ = ['to_pd_timestamp', 'to_timestamp', 'now_timestamp', 'now_pd_timestamp', 'to_time_str', 'now_time_str',
           'next_date', 'is_same_date', 'is_same_time', 'get_year_quarter', 'day_offset_today', 'get_year_quarters',
           'date_and_time', 'next_timestamp', 'evaluate_size_from_timestamp', 'is_finished_kdata_timestamp',
           'is_in_same_interval']
