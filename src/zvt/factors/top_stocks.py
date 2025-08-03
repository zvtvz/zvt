# -*- coding: utf-8 -*-
import json
import logging
from typing import List

from sqlalchemy import Column, String, Integer
from sqlalchemy.orm import declarative_base

from zvt.api.kdata import get_trade_dates, get_kdata_schema
from zvt.api.selector import (
    get_entity_ids_by_filter,
    get_limit_up_stocks,
    get_mini_and_small_stock,
    get_middle_and_big_stock,
)
from zvt.api.stats import get_top_performance_entities_by_periods, TopType
from zvt.contract import Mixin, AdjustType
from zvt.contract.api import get_db_session
from zvt.contract.factor import TargetType
from zvt.contract.register import register_schema
from zvt.domain import Stock
from zvt.factors.ma.ma_factor import VolumeUpMaFactor
from zvt.utils.time_utils import (
    date_time_by_interval,
    to_pd_timestamp,
    to_date_time_str,
    TIME_FORMAT_DAY,
    next_date,
)

logger = logging.getLogger(__name__)

TopStocksBase = declarative_base()


class TopStocks(TopStocksBase, Mixin):
    __tablename__ = "top_stocks"
    entity_type = Column(String(length=64))

    short_count = Column(Integer)
    short_stocks = Column(String(length=2048))

    long_count = Column(Integer)
    long_stocks = Column(String(length=2048))

    small_vol_up_count = Column(Integer)
    small_vol_up_stocks = Column(String(length=2048))

    big_vol_up_count = Column(Integer)
    big_vol_up_stocks = Column(String(length=2048))

    all_stocks_count = Column(Integer)


register_schema(providers=["zvt"], db_name="top_stocks", schema_base=TopStocksBase)


def get_vol_up_stocks(target_date, provider="em", adjust_type=AdjustType.qfq, stock_type="small", entity_ids=None):
    if stock_type == "small":
        current_entity_pool = get_mini_and_small_stock(
            timestamp=target_date, provider=provider, adjust_type=adjust_type
        )
        turnover_threshold = 300000000
        turnover_rate_threshold = 0.02
    elif stock_type == "big":
        current_entity_pool = get_middle_and_big_stock(
            timestamp=target_date, provider=provider, adjust_type=adjust_type
        )
        turnover_threshold = 300000000
        turnover_rate_threshold = 0.01
    else:
        assert False

    if entity_ids:
        current_entity_pool = set(current_entity_pool) & set(entity_ids)

    kdata_schema = get_kdata_schema(entity_type="stock", level="1d", adjust_type=adjust_type)
    filters = [
        kdata_schema.timestamp == to_pd_timestamp(target_date),
        kdata_schema.turnover >= turnover_threshold,
        kdata_schema.turnover_rate >= turnover_rate_threshold,
    ]
    kdata_df = kdata_schema.query_data(
        provider=provider, filters=filters, columns=["entity_id", "timestamp"], index="entity_id"
    )
    if current_entity_pool:
        current_entity_pool = set(current_entity_pool) & set(kdata_df.index.tolist())
    else:
        current_entity_pool = kdata_df.index.tolist()

    factor = VolumeUpMaFactor(
        entity_schema=Stock,
        entity_provider=provider,
        provider=provider,
        entity_ids=current_entity_pool,
        start_timestamp=date_time_by_interval(target_date, -600),
        end_timestamp=target_date,
        adjust_type=adjust_type,
        windows=[120, 250],
        over_mode="or",
        up_intervals=60,
        turnover_threshold=turnover_threshold,
        turnover_rate_threshold=turnover_rate_threshold,
    )

    stocks = factor.get_targets(timestamp=target_date, target_type=TargetType.positive)
    return stocks


def compute_top_stocks(start_date, entity_type="stock", provider="em", force_update=False, adjust_type=AdjustType.qfq):
    session = get_db_session(provider="zvt", data_schema=TopStocks)
    if force_update:
        session.query(TopStocks).filter(TopStocks.timestamp >= start_date).filter(
            TopStocks.entity_type == entity_type
        ).delete()
    else:
        latest = TopStocks.query_data(
            limit=1,
            filters=[TopStocks.entity_type == entity_type],
            order=TopStocks.timestamp.desc(),
            return_type="domain",
        )
        if latest:
            start_date = next_date(the_time=to_date_time_str(latest[0].timestamp, fmt=TIME_FORMAT_DAY))

    trade_days = get_trade_dates(entity_type=entity_type, start=start_date)

    for target_date in trade_days:
        top_stocks = TopStocks(
            entity_type=entity_type,
            entity_id=f"{entity_type}_top",
            id=f"{entity_type}_top_{target_date}",
            timestamp=target_date,
        )

        entity_ids = get_entity_ids_by_filter(
            entity_type=entity_type,
            target_date=target_date,
            provider="em",
        )

        turnover_threshold = 0
        if entity_type == "stockus" or entity_type == "stockhk":
            turnover_threshold = 10000000

        short_selected, short_period = get_top_performance_entities_by_periods(
            entity_provider="em",
            data_provider=provider,
            target_date=target_date,
            periods=[*range(1, 20)],
            ignore_new_stock=False,
            ignore_st=False,
            entity_ids=entity_ids,
            entity_type=entity_type,
            adjust_type=adjust_type,
            top_count=30,
            turnover_threshold=turnover_threshold,
            turnover_rate_threshold=0,
            return_type=TopType.positive,
        )
        if entity_type == "stock":
            limit_up_stocks = get_limit_up_stocks(timestamp=target_date)
            short_selected = list(set(short_selected + limit_up_stocks))
        top_stocks.short_count = len(short_selected)
        top_stocks.short_stocks = json.dumps(short_selected, ensure_ascii=False)

        long_period_start = short_period + 1
        long_selected, long_period = get_top_performance_entities_by_periods(
            entity_provider="em",
            data_provider=provider,
            target_date=target_date,
            periods=[*range(long_period_start, long_period_start + 30)],
            ignore_new_stock=False,
            ignore_st=False,
            entity_ids=entity_ids,
            entity_type=entity_type,
            adjust_type=adjust_type,
            top_count=30,
            turnover_threshold=turnover_threshold,
            turnover_rate_threshold=0,
            return_type=TopType.positive,
        )
        top_stocks.long_count = len(long_selected)
        top_stocks.long_stocks = json.dumps(long_selected, ensure_ascii=False)

        if entity_type == "stock":
            small_vol_up_stocks = get_vol_up_stocks(
                target_date=target_date, provider=provider, stock_type="small", entity_ids=entity_ids
            )
            top_stocks.small_vol_up_count = len(small_vol_up_stocks)
            top_stocks.small_vol_up_stocks = json.dumps(small_vol_up_stocks, ensure_ascii=False)

            big_vol_up_stocks = get_vol_up_stocks(
                target_date=target_date, provider=provider, stock_type="big", entity_ids=entity_ids
            )
            top_stocks.big_vol_up_count = len(big_vol_up_stocks)
            top_stocks.big_vol_up_stocks = json.dumps(big_vol_up_stocks, ensure_ascii=False)

        top_stocks.all_stocks_count = len(entity_ids)

        session.add(top_stocks)
        session.commit()


def get_top_stocks(target_date, entity_type="stock", return_type="short"):
    datas: List[TopStocks] = TopStocks.query_data(
        filters=[TopStocks.entity_type == entity_type, TopStocks.timestamp == to_pd_timestamp(target_date)],
        return_type="domain",
    )
    stocks = []
    if datas:
        assert len(datas) == 1
        top_stock = datas[0]
        if return_type == "all":
            short_stocks = json.loads(top_stock.short_stocks) if top_stock.short_stocks else []
            long_stocks = json.loads(top_stock.long_stocks) if top_stock.long_stocks else []
            small_vol_up_stocks = json.loads(top_stock.small_vol_up_stocks) if top_stock.small_vol_up_stocks else []
            big_vol_up_stocks = json.loads(top_stock.big_vol_up_stocks) if top_stock.big_vol_up_stocks else []
            all_stocks = list(set(short_stocks + long_stocks + small_vol_up_stocks + big_vol_up_stocks))
            return all_stocks
        elif return_type == "short":
            stocks = json.loads(top_stock.short_stocks) if top_stock.short_stocks else []
        elif return_type == "long":
            stocks = json.loads(top_stock.long_stocks) if top_stock.long_stocks else []
        elif return_type == "small_vol_up":
            stocks = json.loads(top_stock.small_vol_up_stocks) if top_stock.small_vol_up_stocks else []
        elif return_type == "big_vol_up":
            stocks = json.loads(top_stock.big_vol_up_stocks) if top_stock.big_vol_up_stocks else []
        else:
            assert False
    return stocks


if __name__ == "__main__":
    print(get_top_stocks(entity_type="stockus", target_date="2025-07-25", return_type="all"))

# the __all__ is generated
__all__ = [
    "TopStocks",
    "get_vol_up_stocks",
    "compute_top_stocks",
    "get_top_stocks",
]
