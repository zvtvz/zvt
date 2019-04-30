# -*- coding: utf-8 -*-

from zvt.api import technical
from zvt.api.common import decode_security_id, get_kdata_schema
from zvt.domain import TradingLevel, Provider, SecurityType


def get_close_column(security_id):
    security_type, _, _ = decode_security_id(security_id)
    data_schema = get_kdata_schema(security_type)

    if security_type == SecurityType.stock:
        columns = [data_schema.security_id, data_schema.timestamp, data_schema.qfq_close]
    else:
        columns = [data_schema.security_id, data_schema.timestamp, data_schema.close]

    return columns


def ma(security_id, start_timestamp, end_timestamp, level=TradingLevel.LEVEL_1DAY, provider=Provider.EASTMONEY,
       window=5):
    df = technical.get_kdata(security_id, start_timestamp=start_timestamp, end_timestamp=end_timestamp,
                             provider=provider,
                             level=level,
                             columns=get_close_column(security_id))

    df = df.rename(columns={'qfq_close': 'close'})

    df['ma_{}'.format(window)] = df['close'].rolling(window=window, min_periods=window).mean()
    return df


def ema(security_id, start_timestamp, end_timestamp, level=TradingLevel.LEVEL_1DAY, provider=Provider.EASTMONEY,
        window=12):
    df = technical.get_kdata(security_id, start_timestamp=start_timestamp, end_timestamp=end_timestamp,
                             provider=provider,
                             level=level,
                             columns=get_close_column(security_id))
    df = df.rename(columns={'qfq_close': 'close'})

    df['ema_{}'.format(window)] = df['close'].ewm(span=window, adjust=False, min_periods=window).mean()

    return df


def macd(security_id, start_timestamp, end_timestamp, level=TradingLevel.LEVEL_1DAY, provider=Provider.EASTMONEY,
         slow=26, fast=12, n=9, return_col=True):
    ema_fast = ema(security_id, start_timestamp, end_timestamp, level=level, provider=provider,
                   window=fast, return_col=return_col)

    ema_slow = ema(security_id, start_timestamp, end_timestamp, level=level, provider=provider,
                   window=slow, return_col=return_col)

    result = ema_fast.copy()
    result["close_ema{}".format(slow)] = ema_slow["close_ema{}".format(slow)]

    result['diff'] = result["close_ema{}".format(fast)] - result["close_ema{}".format(slow)]
    result['dea'] = result['diff'].ewm(span=n, adjust=False).mean()
    result['macd'] = (result['diff'] - result['dea']) * 2

    return result


if __name__ == '__main__':
    print(ma(security_id='stock_sz_002937', start_timestamp='2018-09-28', end_timestamp='2019-12-31',
             provider=Provider.SINA))
    # print(ema(security_item='000002', start_date='20171101', end_date='20171201'))
    # print(ema(get_security_item('000001'), start='20171101', end='20171201'))
    # print(macd(security_id='stock_sz_000002', start_timestamp='20170101', end_timestamp='20171201'))
