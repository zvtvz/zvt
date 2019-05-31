# -*- coding: utf-8 -*-
from zvt.api.technical import get_kdata


def ma(s, window=5):
    """

    :param s:
    :type s:pd.Series
    :param window:
    :type window:
    :return:
    :rtype:
    """
    return s.rolling(window=window, min_periods=window).mean()


def ema(s, window=12):
    return s.ewm(span=window, adjust=False, min_periods=window).mean()


def macd(s, slow=26, fast=12, n=9):
    ema_fast = ema(s, window=fast)

    ema_slow = ema(s, window=slow)

    diff = ema_fast - ema_slow
    dea = diff.ewm(span=n, adjust=False).mean()
    m = (diff - dea) * 2

    return diff, dea, m


if __name__ == '__main__':
    kdata = get_kdata(security_id='stock_sz_000338', start_timestamp='2019-01-01', end_timestamp='2019-05-25',
                      provider='netease')
    kdata['diff'], kdata['dea'], kdata['m'] = macd(kdata['qfq_close'])

    print(kdata)
