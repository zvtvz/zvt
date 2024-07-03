# -*- coding: utf-8 -*-
import logging
from typing import List

import pandas as pd
import sqlalchemy

from zvt.contract.api import df_to_db, get_db_session
from zvt.domain import Stock1dHfqKdata
from zvt.factors.top_stocks import TopStocks, get_top_stocks
from zvt.tag.tag_models import CreateStockPoolsModel
from zvt.tag.tag_schemas import TagStats, StockTags, StockPools
from zvt.tag.tag_service import build_stock_pool
from zvt.utils.pd_utils import pd_is_not_null
from zvt.utils.time_utils import to_pd_timestamp, date_time_by_interval

logger = logging.getLogger(__name__)


def build_system_stock_pools():
    for stock_pool_name in ["main_line", "vol_up", "大局"]:
        datas = StockPools.query_data(
            limit=1,
            filters=[StockPools.stock_pool_name == stock_pool_name],
            order=StockPools.timestamp.desc(),
            return_type="domain",
        )
        start = None
        if datas:
            start = date_time_by_interval(datas[0].timestamp)

        df = TopStocks.query_data(start_timestamp=start, columns=[TopStocks.timestamp], order=TopStocks.timestamp.asc())
        if not pd_is_not_null(df):
            logger.info(f"no data for top_stocks {start}")
            continue
        dates = df["timestamp"].tolist()
        for target_date in dates:
            logger.info(f"build_system_stock_pools {stock_pool_name} to {target_date}")
            if stock_pool_name == "main_line":
                short_stocks = get_top_stocks(target_date=target_date, return_type="short")
                long_stocks = get_top_stocks(target_date=target_date, return_type="long")
                entity_ids = list(set(short_stocks + long_stocks))
            elif stock_pool_name == "vol_up":
                small_stocks = get_top_stocks(target_date=target_date, return_type="small_vol_up")
                big_stocks = get_top_stocks(target_date=target_date, return_type="big_vol_up")
                entity_ids = list(set(small_stocks + big_stocks))
            elif stock_pool_name == "大局":
                entity_ids = get_top_stocks(target_date=target_date, return_type="all")
            else:
                assert False

            kdata_df = Stock1dHfqKdata.query_data(
                provider="em",
                filters=[
                    Stock1dHfqKdata.timestamp == to_pd_timestamp(target_date),
                    Stock1dHfqKdata.entity_id.in_(entity_ids),
                ],
                columns=["entity_id", "turnover"],
                order=Stock1dHfqKdata.turnover.desc(),
            )
            entity_ids = kdata_df["entity_id"].tolist()
            create_stock_pools_model: CreateStockPoolsModel = CreateStockPoolsModel(
                stock_pool_name=stock_pool_name, entity_ids=entity_ids
            )
            build_stock_pool(create_stock_pools_model, target_date=target_date)


def build_stock_pool_tag_stats(stock_pool_name, force_rebuild_latest=False):
    datas = TagStats.query_data(
        limit=1,
        filters=[TagStats.stock_pool_name == stock_pool_name],
        order=TagStats.timestamp.desc(),
        return_type="domain",
    )
    start = None
    current_df = None
    if datas:
        if force_rebuild_latest:
            session = get_db_session("zvt", data_schema=TagStats)
            session.query(TagStats).filter(TagStats.stock_pool_name == stock_pool_name).filter(
                TagStats.timestamp == datas[0].timestamp
            ).delete()
            session.commit()
            return build_stock_pool_tag_stats(stock_pool_name=stock_pool_name, force_rebuild_latest=False)

        latest_tag_stats_timestamp = datas[0].timestamp
        current_df = TagStats.query_data(
            filters=[TagStats.stock_pool_name == stock_pool_name, TagStats.timestamp == latest_tag_stats_timestamp]
        )
        start = date_time_by_interval(latest_tag_stats_timestamp)

    stock_pools: List[StockPools] = StockPools.query_data(
        start_timestamp=start,
        filters=[StockPools.stock_pool_name == stock_pool_name],
        order=StockPools.timestamp.asc(),
        return_type="domain",
    )
    if not stock_pools:
        logger.info(f"no data for {stock_pool_name} {start}")
        return

    for stock_pool in stock_pools:
        target_date = stock_pool.timestamp
        logger.info(f"build_stock_pool_tag_stats for {stock_pool_name} {target_date}")

        entity_ids = stock_pool.entity_ids
        tags_df = StockTags.query_data(entity_ids=entity_ids, return_type="df", index="entity_id")
        kdata_df = Stock1dHfqKdata.query_data(
            provider="em",
            entity_ids=entity_ids,
            filters=[Stock1dHfqKdata.timestamp == to_pd_timestamp(target_date)],
            columns=[Stock1dHfqKdata.entity_id, Stock1dHfqKdata.name, Stock1dHfqKdata.turnover],
            index="entity_id",
        )

        df = pd.concat([tags_df, kdata_df[["turnover", "name"]]], axis=1)

        grouped_df = (
            df.groupby("main_tag")
            .agg(
                turnover=("turnover", "sum"),
                entity_count=("entity_id", "count"),
                entity_ids=("entity_id", lambda entity_id: list(entity_id)),
            )
            .reset_index()
        )
        sorted_df = grouped_df.sort_values(by=["turnover", "entity_count"], ascending=[False, False])
        sorted_df = sorted_df.reset_index(drop=True)
        sorted_df["position"] = sorted_df.index
        sorted_df["is_main_line"] = sorted_df.index < 5
        sorted_df["main_line_continuous_days"] = sorted_df["is_main_line"].apply(lambda x: 1 if x else 0)
        # logger.info(f"current_df\n: {current_df}")
        if pd_is_not_null(current_df):
            sorted_df.set_index("main_tag", inplace=True, drop=False)
            current_df.set_index("main_tag", inplace=True, drop=False)
            common_index = sorted_df[sorted_df["is_main_line"]].index.intersection(
                current_df[current_df["is_main_line"]].index
            )
            pre_selected = current_df.loc[common_index]
            if pd_is_not_null(pre_selected):
                pre_selected = pre_selected.reindex(sorted_df.index, fill_value=0)
                sorted_df["main_line_continuous_days"] = (
                    sorted_df["main_line_continuous_days"] + pre_selected["main_line_continuous_days"]
                )
        sorted_df["entity_id"] = "admin"
        sorted_df["timestamp"] = target_date
        sorted_df["stock_pool_name"] = stock_pool_name
        sorted_df["id"] = sorted_df[["entity_id", "timestamp", "stock_pool_name", "main_tag"]].apply(
            lambda x: "_".join(x.astype(str)), axis=1
        )
        df_to_db(
            provider="zvt",
            df=sorted_df,
            data_schema=TagStats,
            force_update=True,
            dtype={"entity_ids": sqlalchemy.JSON},
        )
        current_df = sorted_df


if __name__ == "__main__":
    # build_system_stock_pools()
    build_stock_pool_tag_stats(stock_pool_name="main_line", force_rebuild_latest=True)
    # build_stock_pool_tag_stats(stock_pool_name="vol_up")


# the __all__ is generated
__all__ = ["build_system_stock_pools", "build_stock_pool_tag_stats"]
