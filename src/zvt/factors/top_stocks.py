# -*- coding: utf-8 -*-
import json
from typing import List

from sqlalchemy import Column, String, Integer
from sqlalchemy.orm import declarative_base

from zvt.api.kdata import get_trade_dates
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
from zvt.domain import Stock, Stock1dHfqKdata
from zvt.factors.ma.ma_factor import VolumeUpMaFactor
from zvt.utils.time_utils import (
    date_time_by_interval,
    to_time_str,
    TIME_FORMAT_DAY,
    today,
    count_interval,
    to_pd_timestamp,
)

TopStocksBase = declarative_base()


class TopStocks(TopStocksBase, Mixin):
    __tablename__ = "top_stocks"

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


def get_vol_up_stocks(target_date, provider="em", stock_type="small", entity_ids=None):
    if stock_type == "small":
        current_entity_pool = get_mini_and_small_stock(timestamp=target_date, provider=provider)
        turnover_threshold = 300000000
        turnover_rate_threshold = 0.02
    elif stock_type == "big":
        current_entity_pool = get_middle_and_big_stock(timestamp=target_date, provider=provider)
        turnover_threshold = 300000000
        turnover_rate_threshold = 0.01
    else:
        assert False

    if entity_ids:
        current_entity_pool = set(current_entity_pool) & set(entity_ids)

    kdata_schema = Stock1dHfqKdata
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
        adjust_type=AdjustType.hfq,
        windows=[120, 250],
        over_mode="or",
        up_intervals=60,
        turnover_threshold=turnover_threshold,
        turnover_rate_threshold=turnover_rate_threshold,
    )

    stocks = factor.get_targets(timestamp=target_date, target_type=TargetType.positive)
    return stocks


def update_with_limit_up():
    session = get_db_session(provider="zvt", data_schema=TopStocks)

    top_stocks: List[TopStocks] = TopStocks.query_data(
        end_timestamp="2021-07-18", return_type="domain", session=session
    )
    for top_stock in top_stocks:
        limit_up_stocks = get_limit_up_stocks(timestamp=top_stock.timestamp)
        short_stocks = json.loads(top_stock.short_stocks)
        stock_list = list(set(short_stocks + limit_up_stocks))
        top_stock.short_stocks = json.dumps(stock_list, ensure_ascii=False)
        top_stock.short_count = len(stock_list)
    session.add_all(top_stocks)
    session.commit()


def update_vol_up():
    session = get_db_session(provider="zvt", data_schema=TopStocks)

    top_stocks: List[TopStocks] = TopStocks.query_data(
        return_type="domain", start_timestamp="2019-03-27", session=session
    )
    for top_stock in top_stocks:
        target_date = top_stock.timestamp
        count_bj = count_interval("2023-09-01", target_date)
        ignore_bj = count_bj < 0

        entity_ids = get_entity_ids_by_filter(
            target_date=target_date,
            provider="em",
            ignore_delist=False,
            ignore_st=False,
            ignore_new_stock=False,
            ignore_bj=ignore_bj,
        )
        small_vol_up_stocks = get_vol_up_stocks(
            target_date=target_date, provider="em", stock_type="small", entity_ids=entity_ids
        )
        top_stock.small_vol_up_count = len(small_vol_up_stocks)
        top_stock.small_vol_up_stocks = json.dumps(small_vol_up_stocks, ensure_ascii=False)

        big_vol_up_stocks = get_vol_up_stocks(
            target_date=target_date, provider="em", stock_type="big", entity_ids=entity_ids
        )
        top_stock.big_vol_up_count = len(big_vol_up_stocks)
        top_stock.big_vol_up_stocks = json.dumps(big_vol_up_stocks, ensure_ascii=False)
        session.add(top_stock)
        session.commit()
        print(f"finish {target_date}")


def compute_top_stocks(provider="em"):
    latest = TopStocks.query_data(limit=1, order=TopStocks.timestamp.desc(), return_type="domain")
    if latest:
        start = date_time_by_interval(to_time_str(latest[0].timestamp, fmt=TIME_FORMAT_DAY))
    else:
        start = "2018-01-01"
    trade_days = get_trade_dates(start=start, end=today())

    for target_date in trade_days:
        print(f"to {target_date}")
        session = get_db_session(provider="zvt", data_schema=TopStocks)
        top_stocks = TopStocks(
            id=f"block_zvt_000001_{target_date}", entity_id="block_zvt_000001", timestamp=target_date
        )

        count_bj = count_interval("2023-09-01", target_date)
        ignore_bj = count_bj < 0

        entity_ids = get_entity_ids_by_filter(
            target_date=target_date,
            provider=provider,
            ignore_delist=False,
            ignore_st=False,
            ignore_new_stock=False,
            ignore_bj=ignore_bj,
        )

        short_selected, short_period = get_top_performance_entities_by_periods(
            entity_provider=provider,
            data_provider=provider,
            target_date=target_date,
            periods=[*range(1, 20)],
            ignore_new_stock=False,
            ignore_st=False,
            entity_ids=entity_ids,
            entity_type="stock",
            adjust_type=None,
            top_count=30,
            turnover_threshold=0,
            turnover_rate_threshold=0,
            return_type=TopType.positive,
        )
        limit_up_stocks = get_limit_up_stocks(timestamp=target_date)
        short_selected = list(set(short_selected + limit_up_stocks))
        top_stocks.short_count = len(short_selected)
        top_stocks.short_stocks = json.dumps(short_selected, ensure_ascii=False)

        long_period_start = short_period + 1
        long_selected, long_period = get_top_performance_entities_by_periods(
            entity_provider=provider,
            data_provider=provider,
            target_date=target_date,
            periods=[*range(long_period_start, long_period_start + 30)],
            ignore_new_stock=False,
            ignore_st=False,
            entity_ids=entity_ids,
            entity_type="stock",
            adjust_type=None,
            top_count=30,
            turnover_threshold=0,
            turnover_rate_threshold=0,
            return_type=TopType.positive,
        )
        top_stocks.long_count = len(long_selected)
        top_stocks.long_stocks = json.dumps(long_selected, ensure_ascii=False)

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

        print(top_stocks)
        session.add(top_stocks)
        session.commit()


def get_top_stocks(target_date, return_type="short"):
    datas: List[TopStocks] = TopStocks.query_data(
        start_timestamp=target_date, end_timestamp=target_date, return_type="domain"
    )
    stocks = []
    if datas:
        assert len(datas) == 1
        top_stock = datas[0]
        if return_type == "all":
            short_stocks = json.loads(top_stock.short_stocks)
            long_stocks = json.loads(top_stock.long_stocks)
            small_vol_up_stocks = json.loads(top_stock.small_vol_up_stocks)
            big_vol_up_stocks = json.loads(top_stock.big_vol_up_stocks)
            all_stocks = list(set(short_stocks + long_stocks + small_vol_up_stocks + big_vol_up_stocks))
            return all_stocks
        elif return_type == "short":
            stocks = json.loads(top_stock.short_stocks)
        elif return_type == "long":
            stocks = json.loads(top_stock.long_stocks)
        elif return_type == "small_vol_up":
            stocks = json.loads(top_stock.small_vol_up_stocks)
        elif return_type == "big_vol_up":
            stocks = json.loads(top_stock.big_vol_up_stocks)
        else:
            assert False
    return stocks


if __name__ == "__main__":
    compute_top_stocks()
    # update_with_limit_up()
    # update_vol_up()
    # target_date = "2024-03-06"
    # stocks = get_top_stocks(target_date=target_date, return_type="short")
    # print(stocks)
    # stocks = get_top_stocks(target_date=target_date, return_type="long")
    # print(stocks)
    # stocks = get_top_stocks(target_date=target_date, return_type="small_vol_up")
    # print(stocks)
    # stocks = get_top_stocks(target_date=target_date, return_type="big_vol_up")
    # print(stocks)


# the __all__ is generated
__all__ = [
    "TopStocks",
    "get_vol_up_stocks",
    "update_with_limit_up",
    "update_vol_up",
    "compute_top_stocks",
    "get_top_stocks",
]
