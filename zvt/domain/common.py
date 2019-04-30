# -*- coding: utf-8 -*-
import enum

from sqlalchemy.ext.declarative import declarative_base

# every base logically means one type of data and physically one db file
MetaBase = declarative_base()

StockKdataBase = declarative_base()

FinanceBase = declarative_base()

BusinessBase = declarative_base()

DividendFinancingBase = declarative_base()

HolderBase = declarative_base()

TradingBase = declarative_base()

MoneyFlowBase = declarative_base()

MacroBase = declarative_base()


class Provider(enum.Enum):
    EASTMONEY = 'eastmoney'
    SINA = 'sina'
    NETEASE = 'netease'
    EXCHANGE = 'exchange'


class StoreCategory(enum.Enum):
    meta = 'meta'
    stock_kdata = 'stock_kdata'
    finance = 'finance'
    dividend_financing = 'dividend_financing'
    holder = 'holder'
    trading = 'trading'
    money_flow = 'money_flow'
    macro = 'macro'
    business = 'business'


store_map_base = {
    StoreCategory.meta: MetaBase,
    StoreCategory.stock_kdata: StockKdataBase,
    StoreCategory.finance: FinanceBase,
    StoreCategory.dividend_financing: DividendFinancingBase,
    StoreCategory.holder: HolderBase,
    StoreCategory.trading: TradingBase,
    StoreCategory.money_flow: MoneyFlowBase,
    StoreCategory.macro: MacroBase,
    StoreCategory.business: BusinessBase,
}


def get_store_category(data_schema):
    if isinstance(data_schema(), MetaBase):
        return StoreCategory.meta
    if isinstance(data_schema(), StockKdataBase):
        return StoreCategory.stock_kdata
    if isinstance(data_schema(), FinanceBase):
        return StoreCategory.finance
    if isinstance(data_schema(), BusinessBase):
        return StoreCategory.business
    if isinstance(data_schema(), DividendFinancingBase):
        return StoreCategory.dividend_financing
    if isinstance(data_schema(), HolderBase):
        return StoreCategory.holder
    if isinstance(data_schema(), TradingBase):
        return StoreCategory.trading
    if isinstance(data_schema(), MacroBase):
        return StoreCategory.macro
    if isinstance(data_schema(), MoneyFlowBase):
        return StoreCategory.money_flow


class SecurityType(enum.Enum):
    stock = 'stock'
    index = 'index'
    coin = 'coin'


class StockCategory(enum.Enum):
    industry = 'industry'
    concept = 'concept'
    area = 'area'
    main = 'main'


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
    LEVEL_1MIN = '1m'
    LEVEL_5MIN = '5m'
    LEVEL_15MIN = '15m'
    LEVEL_30MIN = '30m'
    LEVEL_1HOUR = '1h'
    LEVEL_4HOUR = '4h'
    LEVEL_1DAY = '1d'
    LEVEL_1WEEK = '1wk'

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

    def to_second(self):
        return int(self.to_ms() / 1000)

    def to_ms(self):
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
