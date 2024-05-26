# -*- coding: utf-8 -*-
import json
import logging
from typing import List, Union

import numpy as np
import pandas as pd
from fastapi_pagination.ext.sqlalchemy import paginate

import zvt.contract.api as contract_api
from zvt.contract import IntervalLevel, AdjustType
from zvt.domain import Stock, StockQuote
from zvt.tag import StockTags, StockPools
from zvt.trader import StockTrader
from zvt.trading.common import ExecutionStatus
from zvt.trading.trading_models import (
    BuildTradingPlanModel,
    QueryTradingPlanModel,
    QueryStockQuoteModel,
    StockQuoteStatsModel,
    StockQuoteModel,
    BuildQueryStockQuoteSettingModel,
)
from zvt.trading.trading_schemas import TradingPlan, QueryStockQuoteSetting
from zvt.utils import to_time_str, to_pd_timestamp, now_pd_timestamp, date_time_by_interval, current_date

logger = logging.getLogger(__name__)


def build_trading_plan(build_trading_plan_model: BuildTradingPlanModel):
    with contract_api.DBSession(provider="zvt", data_schema=TradingPlan)() as session:
        stock_id = build_trading_plan_model.stock_id
        trading_date_str = to_time_str(build_trading_plan_model.trading_date)
        trading_date = to_pd_timestamp(trading_date_str)
        signal = build_trading_plan_model.trading_signal_type.value
        plan_id = f"{stock_id}_{trading_date_str}_{signal}"

        datas = TradingPlan.query_data(
            session=session, filters=[TradingPlan.id == plan_id], limit=1, return_type="domain"
        )
        if datas:
            assert len(datas) == 1
            plan = datas[0]
        else:
            datas = Stock.query_data(provider="em", entity_id=stock_id, return_type="domain")
            stock = datas[0]
            plan = TradingPlan(
                id=plan_id,
                entity_id=stock_id,
                stock_id=stock_id,
                stock_code=stock.code,
                stock_name=stock.name,
                trading_date=trading_date,
                expected_open_pct=build_trading_plan_model.expected_open_pct,
                buy_price=build_trading_plan_model.buy_price,
                sell_price=build_trading_plan_model.sell_price,
                trading_reason=build_trading_plan_model.trading_reason,
                trading_signal_type=signal,
                status=ExecutionStatus.init.value,
            )
        plan.timestamp = now_pd_timestamp()
        session.add(plan)
        session.commit()
        session.refresh(plan)
        return plan


def query_trading_plan(query_trading_plan_model: QueryTradingPlanModel):
    with contract_api.DBSession(provider="zvt", data_schema=TradingPlan)() as session:
        time_range = query_trading_plan_model.time_range
        if time_range.relative_time_range:
            start_timestamp = date_time_by_interval(
                current_date(), time_range.relative_time_range.interval, time_range.relative_time_range.time_unit
            )
            end_timestamp = None
        else:
            start_timestamp = time_range.absolute_time_range.start_timestamp
            end_timestamp = time_range.absolute_time_range.end_timestamp
        selectable = TradingPlan.query_data(
            session=session, start_timestamp=start_timestamp, end_timestamp=end_timestamp, return_type="select"
        )
        return paginate(session, selectable)


def get_current_trading_plan():
    with contract_api.DBSession(provider="zvt", data_schema=TradingPlan)() as session:
        return TradingPlan.query_data(
            session=session,
            filters=[TradingPlan.status == ExecutionStatus.pending.value],
            order=TradingPlan.trading_date.asc(),
            return_type="domain",
        )


def get_future_trading_plan():
    with contract_api.DBSession(provider="zvt", data_schema=TradingPlan)() as session:
        return TradingPlan.query_data(
            session=session,
            filters=[TradingPlan.status == ExecutionStatus.init.value],
            order=TradingPlan.trading_date.asc(),
            return_type="domain",
        )


def check_trading_plan():
    with contract_api.DBSession(provider="zvt", data_schema=TradingPlan)() as session:
        plans = TradingPlan.query_data(
            session=session,
            filters=[TradingPlan.status == ExecutionStatus.init.value, TradingPlan.trading_date == current_date()],
            order=TradingPlan.trading_date.asc(),
            return_type="domain",
        )

        logger.info(f"current plans:{plans}")


def query_stock_quotes(query_stock_quote_model: QueryStockQuoteModel):
    entity_ids = None
    if query_stock_quote_model.stock_pool_name:
        stock_pools: List[StockPools] = StockPools.query_data(
            filters=[StockPools.stock_pool_name == query_stock_quote_model.stock_pool_name],
            order=StockPools.timestamp.desc(),
            limit=1,
            return_type="domain",
        )
        if stock_pools:
            entity_ids = stock_pools[0].entity_ids
    else:
        entity_ids = query_stock_quote_model.entity_ids

    if query_stock_quote_model.main_tag:
        tags_dict = StockTags.query_data(
            entity_ids=entity_ids,
            filters=[StockTags.main_tag == query_stock_quote_model.main_tag],
            return_type="dict",
        )
        if not tags_dict:
            return []
        entity_ids = [item["entity_id"] for item in tags_dict]
    else:
        tags_dict = StockTags.query_data(
            return_type="dict",
        )

    entity_tags_map = {item["entity_id"]: item for item in tags_dict}

    order = eval(f"StockQuote.{query_stock_quote_model.order_by_field}.{query_stock_quote_model.order_by_type.value}()")

    quotes = StockQuote.query_data(
        order=order, entity_ids=entity_ids, limit=query_stock_quote_model.limit, return_type="dict"
    )

    df = pd.DataFrame.from_records(data=quotes)

    def set_tags(quote):
        entity_id = quote["entity_id"]
        main_tag = entity_tags_map.get(entity_id, {}).get("main_tag", None)
        sub_tag = entity_tags_map.get(entity_id, {}).get("sub_tag", None)
        return pd.Series({"main_tag": main_tag, "sub_tag": sub_tag})

    df[["main_tag", "sub_tag"]] = df.apply(set_tags, axis=1)

    up_count = (df["change_pct"] > 0).sum()
    down_count = (df["change_pct"] < 0).sum()
    turnover = df["turnover"].sum()
    change_pct = df["change_pct"].mean()
    limit_up_count = df["is_limit_up"].sum()
    limit_down_count = df["is_limit_down"].sum()

    result = {
        "up_count": up_count,
        "down_count": down_count,
        "turnover": turnover,
        "change_pct": change_pct,
        "limit_up_count": limit_up_count,
        "limit_down_count": limit_down_count,
        "quotes": quotes,
    }
    print(result)

    return result


def buy_stocks():
    pass


def sell_stocks():
    pass


def build_query_stock_quote_setting(build_query_stock_quote_setting_model: BuildQueryStockQuoteSettingModel, timestamp):
    with contract_api.DBSession(provider="zvt", data_schema=QueryStockQuoteSetting)() as session:
        the_id = "admin_setting"
        datas = QueryStockQuoteSetting.query_data(ids=[the_id], session=session, return_type="domain")
        if datas:
            stock_pool_info = datas[0]
        else:
            stock_pool_info = QueryStockQuoteSetting(entity_id="admin", id=the_id)
        stock_pool_info.timestamp = to_pd_timestamp(timestamp)
        stock_pool_info.stock_pool_name = build_query_stock_quote_setting_model.stock_pool_name
        stock_pool_info.main_tags = build_query_stock_quote_setting_model.main_tags
        session.add(stock_pool_info)
        session.commit()
        session.refresh(stock_pool_info)
        return stock_pool_info
