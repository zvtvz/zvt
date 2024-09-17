# -*- coding: utf-8 -*-
import logging
from typing import List

import pandas as pd
from fastapi_pagination.ext.sqlalchemy import paginate

import zvt.api.kdata as kdata_api
import zvt.contract.api as contract_api
from zvt.common.query_models import TimeUnit
from zvt.domain import Stock, StockQuote, Stock1mQuote
from zvt.tag.tag_schemas import StockTags, StockPools
from zvt.trading.common import ExecutionStatus
from zvt.trading.trading_models import (
    BuildTradingPlanModel,
    QueryTradingPlanModel,
    QueryTagQuoteModel,
    QueryStockQuoteModel,
    BuildQueryStockQuoteSettingModel,
    KdataRequestModel,
    TSRequestModel,
)
from zvt.trading.trading_schemas import TradingPlan, QueryStockQuoteSetting
from zvt.utils.pd_utils import pd_is_not_null
from zvt.utils.time_utils import (
    to_time_str,
    to_pd_timestamp,
    now_pd_timestamp,
    date_time_by_interval,
    current_date,
    date_and_time,
)

logger = logging.getLogger(__name__)


def query_kdata(kdata_request_model: KdataRequestModel):
    kdata_df = kdata_api.get_kdata(
        entity_ids=kdata_request_model.entity_ids,
        provider=kdata_request_model.data_provider,
        start_timestamp=kdata_request_model.start_timestamp,
        end_timestamp=kdata_request_model.end_timestamp,
        adjust_type=kdata_request_model.adjust_type,
    )
    if pd_is_not_null(kdata_df):
        kdata_df["timestamp"] = kdata_df["timestamp"].apply(lambda x: int(x.timestamp()))
        kdata_df["data"] = kdata_df.apply(
            lambda x: x[
                ["timestamp", "open", "high", "low", "close", "volume", "turnover", "change_pct", "turnover_rate"]
            ].values.tolist(),
            axis=1,
        )
        df = kdata_df.groupby("entity_id").agg(
            code=("code", "first"),
            name=("name", "first"),
            level=("level", "first"),
            datas=("data", lambda data: list(data)),
        )
        df = df.reset_index(drop=False)
        return df.to_dict(orient="records")


def query_ts(ts_request_model: TSRequestModel):
    trading_dates = kdata_api.get_recent_trade_dates(days_count=ts_request_model.days_count)
    ts_df = Stock1mQuote.query_data(
        entity_ids=ts_request_model.entity_ids,
        provider=ts_request_model.data_provider,
        start_timestamp=trading_dates[0],
    )
    if pd_is_not_null(ts_df):
        ts_df["data"] = ts_df.apply(
            lambda x: x[
                ["time", "price", "avg_price", "change_pct", "volume", "turnover", "turnover_rate"]
            ].values.tolist(),
            axis=1,
        )
        df = ts_df.groupby("entity_id").agg(
            code=("code", "first"),
            name=("name", "first"),
            datas=("data", lambda data: list(data)),
        )
        df = df.reset_index(drop=False)
        return df.to_dict(orient="records")


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

        logger.debug(f"current plans:{plans}")


def query_quote_stats():
    quote_df = StockQuote.query_data(
        return_type="df",
        filters=[StockQuote.change_pct >= -0.31, StockQuote.change_pct <= 0.31],
        columns=["timestamp", "entity_id", "time", "change_pct", "turnover", "is_limit_up", "is_limit_down"],
    )
    current_stats = cal_quote_stats(quote_df)
    start_timestamp = current_stats["timestamp"]

    pre_date_df = Stock1mQuote.query_data(
        filters=[Stock1mQuote.timestamp < to_time_str(start_timestamp)],
        order=Stock1mQuote.timestamp.desc(),
        limit=1,
        columns=["timestamp"],
    )
    pre_date = pre_date_df["timestamp"].tolist()[0]

    if start_timestamp.hour >= 15:
        start_timestamp = date_and_time(pre_date, "15:00")
    else:
        start_timestamp = date_and_time(pre_date, f"{start_timestamp.hour}:{start_timestamp.minute}")
    end_timestamp = date_time_by_interval(start_timestamp, 1, TimeUnit.minute)

    pre_df = Stock1mQuote.query_data(
        return_type="df",
        start_timestamp=start_timestamp,
        end_timestamp=end_timestamp,
        filters=[Stock1mQuote.change_pct >= -0.31, Stock1mQuote.change_pct <= 0.31],
        columns=["timestamp", "entity_id", "time", "change_pct", "turnover", "is_limit_up", "is_limit_down"],
    )

    if pd_is_not_null(pre_df):
        pre_stats = cal_quote_stats(pre_df)
        current_stats["pre_turnover"] = pre_stats["turnover"]
        current_stats["turnover_change"] = current_stats["turnover"] - current_stats["pre_turnover"]
    return current_stats


def cal_quote_stats(quote_df):
    quote_df["ss"] = 1

    df = (
        quote_df.groupby("ss")
        .agg(
            timestamp=("timestamp", "last"),
            time=("time", "last"),
            up_count=("change_pct", lambda x: (x > 0).sum()),
            down_count=("change_pct", lambda x: (x <= 0).sum()),
            turnover=("turnover", "sum"),
            change_pct=("change_pct", "mean"),
            limit_up_count=("is_limit_up", "sum"),
            limit_down_count=("is_limit_down", lambda x: (x == True).sum()),
        )
        .reset_index(drop=True)
    )

    return df.to_dict(orient="records")[0]


def query_tag_quotes(query_tag_quote_model: QueryTagQuoteModel):
    stock_pools: List[StockPools] = StockPools.query_data(
        filters=[StockPools.stock_pool_name == query_tag_quote_model.stock_pool_name],
        order=StockPools.timestamp.desc(),
        limit=1,
        return_type="domain",
    )
    if stock_pools:
        entity_ids = stock_pools[0].entity_ids
    else:
        entity_ids = None

    tag_df = StockTags.query_data(
        entity_ids=entity_ids,
        filters=[StockTags.main_tag.in_(query_tag_quote_model.main_tags)],
        columns=[StockTags.entity_id, StockTags.main_tag],
        return_type="df",
        index="entity_id",
    )

    entity_ids = tag_df["entity_id"].tolist()

    quote_df = StockQuote.query_data(entity_ids=entity_ids, return_type="df", index="entity_id")

    df = pd.concat([tag_df, quote_df], axis=1)
    grouped_df = (
        df.groupby("main_tag")
        .agg(
            up_count=("change_pct", lambda x: (x > 0).sum()),
            down_count=("change_pct", lambda x: (x <= 0).sum()),
            turnover=("turnover", "sum"),
            change_pct=("change_pct", "mean"),
            limit_up_count=("is_limit_up", "sum"),
            limit_down_count=("is_limit_down", lambda x: (x == True).sum()),
            total_count=("main_tag", "size"),  # 添加计数，计算每个分组的总行数
        )
        .reset_index(drop=False)
    )
    sorted_df = grouped_df.sort_values(by=["turnover", "total_count"], ascending=[False, False])

    return sorted_df.to_dict(orient="records")


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
            return None
        entity_ids = [item["entity_id"] for item in tags_dict]
    else:
        tags_dict = StockTags.query_data(
            return_type="dict",
        )

    entity_tags_map = {item["entity_id"]: item for item in tags_dict}

    order = eval(f"StockQuote.{query_stock_quote_model.order_by_field}.{query_stock_quote_model.order_by_type.value}()")

    df = StockQuote.query_data(order=order, entity_ids=entity_ids, return_type="df")

    if not pd_is_not_null(df):
        return None

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

    quotes = df.to_dict(orient="records")

    result = {
        "up_count": up_count,
        "down_count": down_count,
        "turnover": turnover,
        "change_pct": change_pct,
        "limit_up_count": limit_up_count,
        "limit_down_count": limit_down_count,
        "quotes": quotes[: query_stock_quote_model.limit],
    }
    return result


def buy_stocks():
    pass


def sell_stocks():
    pass


def build_query_stock_quote_setting(build_query_stock_quote_setting_model: BuildQueryStockQuoteSettingModel):
    with contract_api.DBSession(provider="zvt", data_schema=QueryStockQuoteSetting)() as session:
        the_id = "admin_setting"
        datas = QueryStockQuoteSetting.query_data(ids=[the_id], session=session, return_type="domain")
        if datas:
            query_setting = datas[0]
        else:
            query_setting = QueryStockQuoteSetting(entity_id="admin", id=the_id)
        query_setting.timestamp = current_date()
        query_setting.stock_pool_name = build_query_stock_quote_setting_model.stock_pool_name
        query_setting.main_tags = build_query_stock_quote_setting_model.main_tags
        session.add(query_setting)
        session.commit()
        session.refresh(query_setting)
        return query_setting


def build_default_query_stock_quote_setting():
    datas = QueryStockQuoteSetting.query_data(ids=["admin_setting"], return_type="domain")
    if datas:
        return
    build_query_stock_quote_setting(BuildQueryStockQuoteSettingModel(stock_pool_name="all", main_tags=["消费电子"]))


if __name__ == "__main__":
    # print(query_tag_quotes(QueryTagQuoteModel(stock_pool_name="all", main_tags=["低空经济", "半导体", "化工", "消费电子"])))
    # print(query_stock_quotes(QueryStockQuoteModel(stock_pool_name="all", main_tag="半导体")))
    print(query_quote_stats())
# the __all__ is generated
__all__ = [
    "build_trading_plan",
    "query_trading_plan",
    "get_current_trading_plan",
    "get_future_trading_plan",
    "check_trading_plan",
    "query_stock_quotes",
    "buy_stocks",
    "sell_stocks",
    "build_query_stock_quote_setting",
]
