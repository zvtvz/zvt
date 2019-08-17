# -*- coding: utf-8 -*-
import datetime

import arrow
import pandas as pd
import tzlocal

CHINA_TZ = 'Asia/Shanghai'

TIME_FORMAT_ISO8601 = "YYYY-MM-DDTHH:mm:ss.SSS"

TIME_FORMAT_DAY = 'YYYY-MM-DD'

TIME_FORMAT_DAY1 = 'YYYYMMDD'

TIME_FORMAT_MINUTE = 'YYYYMMDDHHmm'

TIME_FORMAT_MINUTE1 = 'HH:mm'


# ms(int) or second(float) or str
def to_pd_timestamp(the_time):
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


def now_pd_timestamp():
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


if __name__ == '__main__':
    print(date_and_time('2019-10-01', '10:00'))
