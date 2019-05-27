# -*- coding: utf-8 -*-
import pandas as pd

from zvt.domain import SecurityType, TradingLevel
from zvt.utils.time_utils import date_and_time, is_same_time, to_time_str, TIME_FORMAT_MINUTE1


def get_trading_intervals(security_type, exchange):
    if type(security_type) == str:
        security_type = SecurityType(security_type)
    if security_type == SecurityType.stock and exchange in ('sh', 'sz'):
        return ('09:30', '11:30'), ('13:00', '15:00')

    if security_type == SecurityType.coin:
        return ('00:00', '23:59')


def generate_finished_timestamps(security_type, exchange, level):
    return [to_time_str(timestamp, fmt=TIME_FORMAT_MINUTE1) for timestamp in
            iterate_timestamps(security_type=security_type, exchange=exchange,
                               start_timestamp='1999-01-01', end_timestamp='1999-01-01', level=level,
                               ignore_unfinished=True)]


def iterate_timestamps(security_type, exchange, start_timestamp: pd.Timestamp, end_timestamp: pd.Timestamp,
                       level=TradingLevel.LEVEL_1DAY, ignore_unfinished=False) -> pd.Timestamp:
    date_range = pd.date_range(start=start_timestamp, end=end_timestamp,
                               freq='B').tolist()

    if level == TradingLevel.LEVEL_1DAY:
        return date_range

    if level == TradingLevel.LEVEL_1HOUR:
        start_end_list = get_trading_intervals(security_type=security_type, exchange=exchange)

        time_ranges = []

        for date in date_range:
            for start_end in start_end_list:
                start = start_end[0]
                end = start_end[1]

                time_range = pd.date_range(start=date_and_time(the_date=date, the_time=start),
                                           end=date_and_time(the_date=date, the_time=end),
                                           freq='1H').tolist()
                if ignore_unfinished:
                    time_ranges += time_range[1:]
                else:
                    time_ranges += time_range
        return time_ranges

    return date_range


def is_open_time(security_type, exchange, timestamp):
    return is_same_time(timestamp, date_and_time(the_date=timestamp,
                                                 the_time=get_trading_intervals(security_type=security_type,
                                                                                exchange=exchange)[0][0]))


def is_close_time(security_type, exchange, timestamp):
    return is_same_time(timestamp, date_and_time(the_date=timestamp,
                                                 the_time=get_trading_intervals(security_type=security_type,
                                                                                exchange=exchange)[-1][-1]))


# use generate_finished_timestamps to generate
china_stock_finished_1h_timstamps = ['10:30', '11:30', '14:00', '15:00']
china_stock_finished_1d_timstamps = ['00:00', '15:00']

china_stock_level_map_finished_timestamps = {
    '1h': china_stock_finished_1h_timstamps,
    '1d': china_stock_finished_1d_timstamps
}


def is_in_finished_timestamps(security_type, exchange, timestamp, level: TradingLevel):
    if type(security_type) == str:
        security_type = SecurityType(security_type)

    if security_type == SecurityType.stock and exchange in ('sh', 'sz'):
        if to_time_str(timestamp, fmt=TIME_FORMAT_MINUTE1) in china_stock_level_map_finished_timestamps.get(
                level.value):
            return True
    return False


if __name__ == '__main__':
    print(is_in_finished_timestamps(security_type='stock', exchange='sh', level=TradingLevel.LEVEL_1HOUR,
                                    timestamp='1999-01-01 15:00'))
    print(generate_finished_timestamps(security_type='stock', exchange='sh', level=TradingLevel.LEVEL_1DAY))
    # print(is_open_time(security_type='stock', exchange='sh', timestamp='2018-01-01 09:30:00'))
    #
    # for timestamp in iterate_timestamps(security_type='stock', exchange='sh', start_timestamp='2019-01-01',
    #                                     end_timestamp='2019-01-05'):
    #     print(timestamp)
    #
    # for timestamp in iterate_timestamps(security_type='stock', exchange='sh', start_timestamp='2019-01-01',
    #                                     end_timestamp='2019-01-05',
    #                                     level=TradingLevel.LEVEL_1HOUR):
    #     print(timestamp)
    #
    # print('..........')
    #
    # for timestamp in iterate_timestamps(security_type='stock', exchange='sh', start_timestamp='2019-01-01',
    #                                     end_timestamp='2019-01-05',
    #                                     level=TradingLevel.LEVEL_1HOUR, ignore_unfinished=True):
    #     print(timestamp)
