# ccxt related transform
from zvdata import IntervalLevel


def to_ccxt_trading_level(trading_level: IntervalLevel):
    return trading_level.value
