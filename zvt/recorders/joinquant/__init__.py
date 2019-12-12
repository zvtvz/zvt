# -*- coding: utf-8 -*-
from zvdata import IntervalLevel


def to_jq_trading_level(trading_level: IntervalLevel):
    if trading_level < IntervalLevel.LEVEL_1HOUR:
        return trading_level.value

    if trading_level == IntervalLevel.LEVEL_1HOUR:
        return '60m'
    if trading_level == IntervalLevel.LEVEL_4HOUR:
        return '240m'
    if trading_level == IntervalLevel.LEVEL_1DAY:
        return '1d'
    if trading_level == IntervalLevel.LEVEL_1WEEK:
        return '1w'
    if trading_level == IntervalLevel.LEVEL_1MON:
        return '1M'


def to_jq_entity_id(security_item):
    if security_item.entity_type == 'stock':
        if security_item.exchange == 'sh':
            return '{}.XSHG'.format(security_item.code)
        if security_item.exchange == 'sz':
            return '{}.XSHE'.format(security_item.code)


from .quotes.jq_stock_kdata_recorder import ChinaStockKdataRecorder
from .macro.margin_trading_recorder import MarginTradingSummaryRecorder
from .macro.cross_market_recorder import CrossMarketSummaryRecorder
from .macro.stock_summary_recorder import StockSummaryRecorder

__all__ = ['ChinaStockKdataRecorder', 'MarginTradingSummaryRecorder', 'CrossMarketSummaryRecorder',
           'StockSummaryRecorder']
