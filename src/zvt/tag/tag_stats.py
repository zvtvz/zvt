# -*- coding: utf-8 -*-
import logging
from typing import List

import pandas as pd
import sqlalchemy

from zvt.api.kdata import get_kdata_schema
from zvt.contract import AdjustType, IntervalLevel
from zvt.contract.api import df_to_db, get_db_session
from zvt.domain.quotes import KdataCommon
from zvt.factors.top_stocks import TopStocks, get_top_stocks
from zvt.tag.common import InsertMode
from zvt.tag.tag_models import CreateStockPoolsModel
from zvt.tag.tag_schemas import TagStats, StockTags, StockPools
from zvt.tag.tag_service import build_stock_pool
from zvt.utils.pd_utils import pd_is_not_null
from zvt.utils.time_utils import to_pd_timestamp, current_date, next_date

logger = logging.getLogger(__name__)


def build_system_stock_pools(start_date, entity_type, force_update=False):
    if entity_type == "stock":
        stock_pool_names = ["主线", "年线", "大局"]
    elif entity_type == "stockus":
        stock_pool_names = ["美股主线"]
    elif entity_type == "stockhk":
        stock_pool_names = ["港股主线"]
    else:
        raise ValueError(f"entity_type {entity_type} not supported")

    for stock_pool_name in stock_pool_names:
        if not force_update:
            datas = StockPools.query_data(
                limit=1,
                filters=[StockPools.entity_type == entity_type, StockPools.stock_pool_name == stock_pool_name],
                order=StockPools.timestamp.desc(),
                return_type="domain",
            )
            if datas:
                start_date = max(next_date(the_time=datas[0].timestamp), start_date)

        df = TopStocks.query_data(
            start_timestamp=start_date,
            filters=[TopStocks.entity_type == entity_type],
            columns=[TopStocks.timestamp],
            order=TopStocks.timestamp.asc(),
        )
        if not pd_is_not_null(df):
            logger.info(f"no data for top_stocks {entity_type} {start_date}")
            continue

        dates = df["timestamp"].tolist()
        for target_date in dates:
            logger.info(f"build_system_stock_pools {entity_type} {stock_pool_name} to {target_date}")
            if stock_pool_name == "主线" or stock_pool_name == "美股主线" or stock_pool_name == "港股主线":
                short_stocks = get_top_stocks(entity_type=entity_type, target_date=target_date, return_type="short")
                long_stocks = get_top_stocks(entity_type=entity_type, target_date=target_date, return_type="long")
                entity_ids = list(set(short_stocks + long_stocks))
            elif stock_pool_name == "年线":
                small_stocks = get_top_stocks(
                    entity_type=entity_type, target_date=target_date, return_type="small_vol_up"
                )
                big_stocks = get_top_stocks(entity_type=entity_type, target_date=target_date, return_type="big_vol_up")
                entity_ids = list(set(small_stocks + big_stocks))
            elif stock_pool_name == "大局":
                entity_ids = get_top_stocks(entity_type=entity_type, target_date=target_date, return_type="all")
            else:
                assert False

            if not entity_ids:
                logger.info(f"no data for {entity_type} {stock_pool_name} {target_date}")
                break

            create_stock_pools_model: CreateStockPoolsModel = CreateStockPoolsModel(
                entity_type=entity_type,
                stock_pool_name=stock_pool_name,
                entity_ids=entity_ids,
                insert_mode=InsertMode.overwrite,
            )
            build_stock_pool(create_stock_pools_model, target_date=target_date)


def build_stock_pool_tag_stats(
    stock_pool_name,
    entity_type="stock",
    force_rebuild_latest=False,
    target_date=None,
    adjust_type=AdjustType.qfq,
    provider="em",
):
    datas = TagStats.query_data(
        limit=1,
        filters=[TagStats.entity_type == entity_type, TagStats.stock_pool_name == stock_pool_name],
        order=TagStats.timestamp.desc(),
        return_type="domain",
    )
    start = target_date
    current_df = None
    if datas:
        if force_rebuild_latest:
            session = get_db_session("zvt", data_schema=TagStats)
            session.query(TagStats).filter(TagStats.entity_type == entity_type).filter(
                TagStats.stock_pool_name == stock_pool_name
            ).filter(TagStats.timestamp == datas[0].timestamp).delete()
            session.commit()
            return build_stock_pool_tag_stats(stock_pool_name=stock_pool_name, force_rebuild_latest=False)

        latest_tag_stats_timestamp = datas[0].timestamp
        current_df = TagStats.query_data(
            filters=[
                TagStats.entity_type == entity_type,
                TagStats.stock_pool_name == stock_pool_name,
                TagStats.timestamp == latest_tag_stats_timestamp,
            ]
        )
        start = next_date(the_time=latest_tag_stats_timestamp)

    stock_pools: List[StockPools] = StockPools.query_data(
        start_timestamp=start,
        filters=[StockPools.entity_type == entity_type, StockPools.stock_pool_name == stock_pool_name],
        order=StockPools.timestamp.asc(),
        return_type="domain",
    )
    if not stock_pools:
        logger.info(f"no data to build tag stats: {entity_type} {stock_pool_name} {start}")
        return None

    for stock_pool in stock_pools:
        target_date = stock_pool.timestamp
        logger.info(f"build_stock_pool_tag_stats for {entity_type} {stock_pool_name} {target_date}")

        entity_ids = stock_pool.entity_ids
        tags_df = StockTags.query_data(
            entity_ids=entity_ids, filters=[StockTags.entity_type == entity_type], return_type="df", index="entity_id"
        )
        kdata_schema: KdataCommon = get_kdata_schema(
            entity_type=entity_type, level=IntervalLevel.LEVEL_1DAY, adjust_type=adjust_type
        )
        kdata_df = kdata_schema.query_data(
            provider=provider,
            entity_ids=entity_ids,
            filters=[kdata_schema.timestamp == to_pd_timestamp(target_date)],
            columns=[kdata_schema.entity_id, kdata_schema.name, kdata_schema.turnover],
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
        # sorted_df = grouped_df.sort_values(by=["entity_count"], ascending=[False])
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
        sorted_df["entity_id"] = f"{entity_type}_{stock_pool_name}"
        sorted_df["timestamp"] = target_date
        sorted_df["entity_type"] = entity_type
        sorted_df["stock_pool_name"] = stock_pool_name
        sorted_df["id"] = sorted_df[["entity_id", "timestamp", "main_tag"]].apply(
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


def refresh_stock_pool(stock_pool_name, entity_ids, insert_mode=InsertMode.append, target_date=current_date()):
    create_stock_pools_model: CreateStockPoolsModel = CreateStockPoolsModel(
        stock_pool_name=stock_pool_name, entity_ids=entity_ids, insert_mode=insert_mode
    )

    build_stock_pool(create_stock_pools_model, target_date=target_date)


def get_tags_order_by_position(stock_pool_name, entity_type="stock"):
    latest_data = TagStats.query_data(
        filters=[TagStats.entity_type == entity_type, TagStats.stock_pool_name == stock_pool_name],
        order=TagStats.timestamp.desc(),
        limit=1,
        return_type="domain",
    )
    target_date = to_pd_timestamp(latest_data[0].timestamp)

    tag_stats_list: List[TagStats] = TagStats.query_data(
        filters=[
            TagStats.timestamp == to_pd_timestamp(target_date),
            TagStats.entity_type == entity_type,
            TagStats.stock_pool_name == stock_pool_name,
        ],
        order=TagStats.position.asc(),
        return_type="domain",
    )

    all_tags = [item.main_tag for item in tag_stats_list]
    main_line_tag1 = all_tags[0:1]
    main_line_tag2 = all_tags[1:2]
    sub_line_tags1 = all_tags[2:4]
    sub_line_tags2 = all_tags[4:6]
    following_tags = all_tags[6:8]
    other_tags = all_tags[8:]
    return main_line_tag1, main_line_tag2, sub_line_tags1, sub_line_tags2, following_tags, other_tags


if __name__ == "__main__":
    # build_system_stock_pools()
    # build_stock_pool_tag_stats(stock_pool_name="主线", force_rebuild_latest=True)
    # build_stock_pool_tag_stats(stock_pool_name="年线")
    print(get_tags_order_by_position(stock_pool_name="主线", entity_type="stockus"))


# the __all__ is generated
__all__ = ["build_system_stock_pools", "build_stock_pool_tag_stats", "refresh_stock_pool"]
