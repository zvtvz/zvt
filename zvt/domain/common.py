# -*- coding: utf-8 -*-
import enum
import math

import pandas as pd
from sqlalchemy.ext.declarative import declarative_base

from zvt.utils.time_utils import to_pd_timestamp

# every base logically means one type of data and physically one db file
MetaBase = declarative_base()

Stock1MKdataBase = declarative_base()
Stock5MKdataBase = declarative_base()
Stock15MKdataBase = declarative_base()
Stock30MKdataBase = declarative_base()
Stock1HKdataBase = declarative_base()
Stock1DKdataBase = declarative_base()
Stock1WKKdataBase = declarative_base()

Index1DKdataBase = declarative_base()

FinanceBase = declarative_base()

BusinessBase = declarative_base()

DividendFinancingBase = declarative_base()

HolderBase = declarative_base()

TradingBase = declarative_base()

MoneyFlowBase = declarative_base()

MacroBase = declarative_base()

CoinMetaBase = declarative_base()

CoinTickKdataBase = declarative_base()
Coin1MKdataBase = declarative_base()
Coin5MKdataBase = declarative_base()
Coin15MKdataBase = declarative_base()
Coin1HKdataBase = declarative_base()
Coin1DKdataBase = declarative_base()
Coin1WKKdataBase = declarative_base()


class Provider(enum.Enum):
    EASTMONEY = 'eastmoney'
    SINA = 'sina'
    NETEASE = 'netease'
    EXCHANGE = 'exchange'
    JOINQUANT = 'joinquant'
    CCXT = 'ccxt'
    ZVT = 'zvt'


class StoreCategory(enum.Enum):
    meta = 'meta'
    stock_1m_kdata = 'stock_1m_kdata'
    stock_5m_kdata = 'stock_5m_kdata'
    stock_15m_kdata = 'stock_15m_kdata'
    stock_1h_kdata = 'stock_1h_kdata'
    stock_1d_kdata = 'stock_1d_kdata'
    stock_1wk_kdata = 'stock_1wk_kdata'

    index_1d_kdata = 'index_1d_kdata'

    finance = 'finance'
    dividend_financing = 'dividend_financing'
    holder = 'holder'
    trading = 'trading'
    money_flow = 'money_flow'
    macro = 'macro'
    business = 'business'

    coin_meta = 'coin_meta'
    coin_tick_kdata = 'coin_tick_kdata'
    coin_1m_kdata = 'coin_1m_kdata'
    coin_5m_kdata = 'coin_5m_kdata'
    coin_15m_kdata = 'coin_15m_kdata'
    coin_1h_kdata = 'coin_1h_kdata'
    coin_1d_kdata = 'coin_1d_kdata'
    coin_1wk_kdata = 'coin_1wk_kdata'


provider_map_category = {
    Provider.EASTMONEY: [StoreCategory.meta,
                         StoreCategory.finance,
                         StoreCategory.dividend_financing,
                         StoreCategory.holder,
                         StoreCategory.trading],

    Provider.SINA: [StoreCategory.meta,
                    StoreCategory.index_1d_kdata,
                    StoreCategory.stock_1d_kdata,
                    StoreCategory.money_flow],

    Provider.NETEASE: [StoreCategory.stock_1d_kdata,
                       StoreCategory.index_1d_kdata],

    Provider.EXCHANGE: [StoreCategory.meta, StoreCategory.macro],

    Provider.ZVT: [StoreCategory.business],

    # TODO:would add other data from joinquant
    Provider.JOINQUANT: [StoreCategory.stock_1m_kdata,
                         StoreCategory.stock_5m_kdata,
                         StoreCategory.stock_15m_kdata,
                         StoreCategory.stock_1h_kdata,
                         StoreCategory.stock_1d_kdata,
                         StoreCategory.stock_1wk_kdata, ],

    Provider.CCXT: [StoreCategory.coin_meta,
                    StoreCategory.coin_tick_kdata,
                    StoreCategory.coin_1m_kdata,
                    StoreCategory.coin_5m_kdata,
                    StoreCategory.coin_15m_kdata,
                    StoreCategory.coin_1h_kdata,
                    StoreCategory.coin_1d_kdata,
                    StoreCategory.coin_1wk_kdata],
}

category_map_db = {
    StoreCategory.meta: MetaBase,
    StoreCategory.stock_1m_kdata: Stock1MKdataBase,
    StoreCategory.stock_5m_kdata: Stock5MKdataBase,
    StoreCategory.stock_15m_kdata: Stock15MKdataBase,
    StoreCategory.stock_1h_kdata: Stock1HKdataBase,
    StoreCategory.stock_1d_kdata: Stock1DKdataBase,
    StoreCategory.stock_1wk_kdata: Stock1WKKdataBase,

    StoreCategory.index_1d_kdata: Index1DKdataBase,
    StoreCategory.finance: FinanceBase,
    StoreCategory.dividend_financing: DividendFinancingBase,
    StoreCategory.holder: HolderBase,
    StoreCategory.trading: TradingBase,
    StoreCategory.money_flow: MoneyFlowBase,
    StoreCategory.macro: MacroBase,
    StoreCategory.business: BusinessBase,

    StoreCategory.coin_meta: CoinMetaBase,
    StoreCategory.coin_tick_kdata: CoinTickKdataBase,
    StoreCategory.coin_1m_kdata: Coin1MKdataBase,
    StoreCategory.coin_5m_kdata: Coin5MKdataBase,
    StoreCategory.coin_15m_kdata: Coin15MKdataBase,
    StoreCategory.coin_1h_kdata: Coin1HKdataBase,
    StoreCategory.coin_1d_kdata: Coin1DKdataBase,
    StoreCategory.coin_1wk_kdata: Coin1WKKdataBase
}


def get_store_category(data_schema):
    for category, base in category_map_db.items():
        if isinstance(data_schema(), base):
            return category


class SecurityType(enum.Enum):
    stock = 'stock'
    index = 'index'
    coin = 'coin'
    future = 'future'


class StockCategory(enum.Enum):
    # 行业版块
    industry = 'industry'
    # 概念版块
    concept = 'concept'
    # 区域版块
    area = 'area'
    # 上证指数
    sse = 'sse'
    # 深圳指数
    szse = 'szse'
    # 中证指数
    csi = 'csi'
    # 国证指数
    cni = 'cni'
    # ETF
    etf = 'etf'


class ReportPeriod(enum.Enum):
    season1 = 'season1'
    half_year = 'half_year'
    season3 = 'seanson3'
    year = 'year'


class InstitutionalInvestor(enum.Enum):
    fund = 'fund'
    social_security = 'social_security'
    insurance = 'insurance'
    qfii = 'qfii'
    trust = 'trust'
    broker = 'broker'


# 用于区分不同的财务指标
class CompanyType(enum.Enum):
    qiye = 'qiye'
    baoxian = 'baoxian'
    yinhang = 'yinhang'
    quanshang = 'quanshang'


class TradingLevel(enum.Enum):
    LEVEL_TICK = 'tick'
    LEVEL_1MIN = '1m'
    LEVEL_5MIN = '5m'
    LEVEL_15MIN = '15m'
    LEVEL_30MIN = '30m'
    LEVEL_1HOUR = '1h'
    LEVEL_4HOUR = '4h'
    LEVEL_1DAY = '1d'
    LEVEL_1WEEK = '1wk'

    def to_pd_freq(self):
        if self == TradingLevel.LEVEL_1MIN:
            return '1min'
        if self == TradingLevel.LEVEL_5MIN:
            return '5min'
        if self == TradingLevel.LEVEL_15MIN:
            return '15min'
        if self == TradingLevel.LEVEL_30MIN:
            return '30min'
        if self == TradingLevel.LEVEL_1HOUR:
            return '1H'
        if self == TradingLevel.LEVEL_4HOUR:
            return '4H'
        if self >= TradingLevel.LEVEL_1DAY:
            return '1D'

    def count_from_timestamp(self, pd_timestamp, one_day_trading_minutes):
        current_time = pd.Timestamp.now()
        time_delta = current_time - pd_timestamp

        one_day_trading_seconds = one_day_trading_minutes * 60

        if time_delta.days > 0:
            seconds = (time_delta.days + 1) * one_day_trading_seconds
            return None, int(math.ceil(seconds / self.to_second())) + 1
        else:
            seconds = time_delta.total_seconds()
            return self.to_second() - seconds, min(int(math.ceil(seconds / self.to_second())) + 1,
                                                   one_day_trading_seconds / self.to_second())

    def floor_timestamp(self, pd_timestamp):
        if self == TradingLevel.LEVEL_1MIN:
            return pd_timestamp.floor('1min')
        if self == TradingLevel.LEVEL_5MIN:
            return pd_timestamp.floor('5min')
        if self == TradingLevel.LEVEL_15MIN:
            return pd_timestamp.floor('15min')
        if self == TradingLevel.LEVEL_30MIN:
            return pd_timestamp.floor('30min')
        if self == TradingLevel.LEVEL_1HOUR:
            return pd_timestamp.floor('1h')
        if self == TradingLevel.LEVEL_4HOUR:
            return pd_timestamp.floor('4h')
        if self >= TradingLevel.LEVEL_1DAY:
            return pd_timestamp.floor('1d')

    def is_last_data_of_day(self, hour, minute, pd_timestamp):
        if self == TradingLevel.LEVEL_1MIN:
            return pd_timestamp.hour == hour and pd_timestamp.minute + 1 == minute
        if self == TradingLevel.LEVEL_5MIN:
            return pd_timestamp.hour == hour and pd_timestamp.minute + 5 == minute
        if self == TradingLevel.LEVEL_15MIN:
            return pd_timestamp.hour == hour and pd_timestamp.minute + 15 == minute
        if self == TradingLevel.LEVEL_30MIN:
            return pd_timestamp.hour == hour and pd_timestamp.minute + 30 == minute
        if self == TradingLevel.LEVEL_1HOUR:
            return pd_timestamp.hour == hour and pd_timestamp.minute + 60 == minute
        if self == TradingLevel.LEVEL_4HOUR:
            return pd_timestamp.hour == hour and pd_timestamp.minute + 240 == minute
        if self >= TradingLevel.LEVEL_1DAY:
            return True

    def to_minute(self):
        return int(self.to_second() / 60)

    def to_second(self):
        return int(self.to_ms() / 1000)

    def to_ms(self):
        # we treat tick intervals is 5s, you could change it
        if self == TradingLevel.LEVEL_TICK:
            return 5 * 1000
        if self == TradingLevel.LEVEL_1MIN:
            return 60 * 1000
        if self == TradingLevel.LEVEL_5MIN:
            return 5 * 60 * 1000
        if self == TradingLevel.LEVEL_15MIN:
            return 15 * 60 * 1000
        if self == TradingLevel.LEVEL_30MIN:
            return 30 * 60 * 1000
        if self == TradingLevel.LEVEL_1HOUR:
            return 60 * 60 * 1000
        if self == TradingLevel.LEVEL_4HOUR:
            return 4 * 60 * 60 * 1000
        if self == TradingLevel.LEVEL_1DAY:
            return 24 * 60 * 60 * 1000
        if self == TradingLevel.LEVEL_1WEEK:
            return 7 * 24 * 60 * 60 * 1000

    def __ge__(self, other):
        if self.__class__ is other.__class__:
            return self.to_ms() >= other.to_ms()
        return NotImplemented

    def __gt__(self, other):

        if self.__class__ is other.__class__:
            return self.to_ms() > other.to_ms()
        return NotImplemented

    def __le__(self, other):
        if self.__class__ is other.__class__:
            return self.to_ms() <= other.to_ms()
        return NotImplemented

    def __lt__(self, other):
        if self.__class__ is other.__class__:
            return self.to_ms() < other.to_ms()
        return NotImplemented


enum_value = lambda x: [e.value for e in x]

COIN_EXCHANGES = ["binance", "huobipro", "okex"]

# COIN_BASE = ["BTC", "ETH", "XRP", "BCH", "EOS", "LTC", "XLM", "ADA", "IOTA", "TRX", "NEO", "DASH", "XMR",
#                        "BNB", "ETC", "QTUM", "ONT"]

COIN_BASE = ["BTC", "ETH", "EOS"]

COIN_PAIRS = [("{}/{}".format(item, "USDT")) for item in COIN_BASE] + \
             [("{}/{}".format(item, "USD")) for item in COIN_BASE]

if __name__ == '__main__':
    # print(provider_map_category.get('eastmoney'))
    print(TradingLevel.LEVEL_1HOUR.count_from_timestamp(to_pd_timestamp('2019-05-31'), 240))
