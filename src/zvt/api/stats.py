# -*- coding: utf-8 -*-
import enum
import itertools
import logging
from typing import Union

import pandas as pd

from zvt.api.kdata import get_kdata_schema, default_adjust_type, get_latest_kdata_date, get_trade_dates
from zvt.api.selector import get_entity_ids_by_filter
from zvt.api.utils import get_recent_report_date
from zvt.contract import Mixin, AdjustType
from zvt.contract.api import decode_entity_id, get_entity_schema, get_entity_ids
from zvt.contract.drawer import Drawer
from zvt.domain import FundStock, StockValuation, BlockStock, Block
from zvt.utils.pd_utils import pd_is_not_null
from zvt.utils.time_utils import (
    month_start_end_ranges,
    to_time_str,
    is_same_date,
    now_pd_timestamp,
    date_time_by_interval,
)

logger = logging.getLogger(__name__)


class WindowMethod(enum.Enum):
    change = "change"
    avg = "avg"
    sum = "sum"


class TopType(enum.Enum):
    positive = "positive"
    negative = "negative"


def get_top_performance_by_month(
    entity_type="stock",
    start_timestamp="2015-01-01",
    end_timestamp=now_pd_timestamp(),
    list_days=None,
    data_provider=None,
):
    ranges = month_start_end_ranges(start_date=start_timestamp, end_date=end_timestamp)

    for month_range in ranges:
        start_timestamp = month_range[0]
        end_timestamp = month_range[1]
        top, _ = get_top_performance_entities(
            entity_type=entity_type,
            start_timestamp=start_timestamp,
            end_timestamp=end_timestamp,
            list_days=list_days,
            data_provider=data_provider,
        )

        yield start_timestamp, end_timestamp, top


def get_top_performance_entities_by_periods(
    entity_provider,
    data_provider,
    target_date=None,
    periods=None,
    ignore_new_stock=True,
    ignore_st=True,
    entity_ids=None,
    entity_type="stock",
    adjust_type=None,
    top_count=50,
    turnover_threshold=100000000,
    turnover_rate_threshold=0.02,
    return_type=TopType.positive,
):
    if periods is None:
        periods = [*range(1, 21)]
    if not adjust_type:
        adjust_type = default_adjust_type(entity_type=entity_type)
    kdata_schema = get_kdata_schema(entity_type=entity_type, adjust_type=adjust_type)
    entity_schema = get_entity_schema(entity_type=entity_type)

    if not target_date:
        target_date = get_latest_kdata_date(provider=data_provider, entity_type=entity_type, adjust_type=adjust_type)

    filter_entity_ids = get_entity_ids_by_filter(
        provider=entity_provider,
        ignore_st=ignore_st,
        ignore_new_stock=ignore_new_stock,
        entity_schema=entity_schema,
        target_date=target_date,
        entity_ids=entity_ids,
    )

    if not filter_entity_ids:
        return []

    filter_turnover_df = kdata_schema.query_data(
        filters=[
            kdata_schema.turnover >= turnover_threshold,
            kdata_schema.turnover_rate >= turnover_rate_threshold,
        ],
        provider=data_provider,
        start_timestamp=date_time_by_interval(target_date, -7),
        end_timestamp=target_date,
        index="entity_id",
        columns=["entity_id", "code"],
    )
    if filter_entity_ids:
        filter_entity_ids = set(filter_entity_ids) & set(filter_turnover_df.index.tolist())
    else:
        filter_entity_ids = filter_turnover_df.index.tolist()

    if not filter_entity_ids:
        return []

    logger.info(f"{entity_type} filter_entity_ids size: {len(filter_entity_ids)}")
    filters = [kdata_schema.entity_id.in_(filter_entity_ids)]
    selected = []
    current_start = None
    real_period = 1
    for i, period in enumerate(periods):
        real_period = max(real_period, period)
        while True:
            start = date_time_by_interval(target_date, -real_period)
            trade_days = get_trade_dates(start=start, end=target_date)
            if not trade_days:
                logger.info(f"no trade days in: {start} to {target_date}")
                real_period = real_period + 1
                continue
            if current_start and is_same_date(current_start, trade_days[0]):
                logger.info("ignore same trade days")
                real_period = real_period + 1
                continue
            break
        current_start = trade_days[0]
        current_end = trade_days[-1]

        logger.info(f"trade days in: {current_start} to {current_end}, real_period: {real_period} ")
        positive_df, negative_df = get_top_performance_entities(
            entity_type=entity_type,
            start_timestamp=current_start,
            end_timestamp=current_end,
            kdata_filters=filters,
            pct=1,
            show_name=True,
            entity_provider=entity_provider,
            data_provider=data_provider,
            return_type=return_type,
        )

        if return_type == TopType.positive:
            df = positive_df
        else:
            df = negative_df
        if pd_is_not_null(df):
            selected = selected + df.index[:top_count].tolist()
            selected = list(dict.fromkeys(selected))
    return selected, real_period


def get_top_performance_entities(
    entity_type="stock",
    start_timestamp=None,
    end_timestamp=None,
    pct=0.1,
    return_type=None,
    adjust_type: Union[AdjustType, str] = None,
    entity_filters=None,
    kdata_filters=None,
    show_name=False,
    list_days=None,
    entity_provider=None,
    data_provider=None,
):
    if not adjust_type:
        adjust_type = default_adjust_type(entity_type=entity_type)
    data_schema = get_kdata_schema(entity_type=entity_type, adjust_type=adjust_type)

    if not entity_filters:
        entity_filters = []
    if list_days:
        entity_schema = get_entity_schema(entity_type=entity_type)
        list_date = date_time_by_interval(start_timestamp, -list_days)
        entity_filters += [entity_schema.list_date <= list_date]

    filter_entities = get_entity_ids(
        provider=entity_provider,
        entity_type=entity_type,
        filters=entity_filters,
    )
    if not filter_entities:
        logger.warning(f"no entities selected")
        return None, None

    if not kdata_filters:
        kdata_filters = []
    kdata_filters = kdata_filters + [data_schema.entity_id.in_(filter_entities)]

    return get_top_entities(
        data_schema=data_schema,
        start_timestamp=start_timestamp,
        end_timestamp=end_timestamp,
        column="close",
        pct=pct,
        method=WindowMethod.change,
        return_type=return_type,
        kdata_filters=kdata_filters,
        show_name=show_name,
        data_provider=data_provider,
    )


def get_top_fund_holding_stocks(timestamp=None, pct=0.3, by=None):
    if not timestamp:
        timestamp = now_pd_timestamp()
    # 季报一般在report_date后1个月内公布，年报2个月内，年报4个月内
    # 所以取时间点的最近的两个公布点，保证取到数据
    # 所以，这是个滞后的数据，只是为了看个大概，毕竟模糊的正确better than 精确的错误
    report_date = get_recent_report_date(timestamp, 1)
    fund_cap_df = FundStock.query_data(
        filters=[
            FundStock.report_date >= report_date,
            FundStock.timestamp <= timestamp,
        ],
        columns=["stock_id", "market_cap"],
    )
    fund_cap_df = fund_cap_df.groupby("stock_id")["market_cap"].sum().sort_values(ascending=False)

    # 直接根据持有市值返回
    if not by:
        s = fund_cap_df.iloc[: int(len(fund_cap_df) * pct)]

        return s.to_frame()

    # 按流通盘比例
    if by == "trading":
        columns = ["entity_id", "circulating_market_cap"]
    # 按市值比例
    elif by == "all":
        columns = ["entity_id", "market_cap"]

    entity_ids = fund_cap_df.index.tolist()
    start_timestamp = date_time_by_interval(timestamp, -30)
    cap_df = StockValuation.query_data(
        entity_ids=entity_ids,
        filters=[
            StockValuation.timestamp >= start_timestamp,
            StockValuation.timestamp <= timestamp,
        ],
        columns=columns,
    )
    if by == "trading":
        cap_df = cap_df.rename(columns={"circulating_market_cap": "cap"})
    elif by == "all":
        cap_df = cap_df.rename(columns={"market_cap": "cap"})

    cap_df = cap_df.groupby("entity_id").mean()
    result_df = pd.concat([cap_df, fund_cap_df], axis=1, join="inner")
    result_df["pct"] = result_df["market_cap"] / result_df["cap"]

    pct_df = result_df["pct"].sort_values(ascending=False)

    s = pct_df.iloc[: int(len(pct_df) * pct)]

    return s.to_frame()


def get_performance(
    entity_ids,
    start_timestamp=None,
    end_timestamp=None,
    adjust_type: Union[AdjustType, str] = None,
    data_provider=None,
):
    entity_type, _, _ = decode_entity_id(entity_ids[0])
    if not adjust_type:
        adjust_type = default_adjust_type(entity_type=entity_type)
    data_schema = get_kdata_schema(entity_type=entity_type, adjust_type=adjust_type)

    result, _ = get_top_entities(
        data_schema=data_schema,
        column="close",
        start_timestamp=start_timestamp,
        end_timestamp=end_timestamp,
        pct=1,
        method=WindowMethod.change,
        return_type=TopType.positive,
        kdata_filters=[data_schema.entity_id.in_(entity_ids)],
        data_provider=data_provider,
    )
    return result


def get_performance_stats_by_month(
    entity_type="stock",
    start_timestamp="2015-01-01",
    end_timestamp=now_pd_timestamp(),
    adjust_type: Union[AdjustType, str] = None,
    data_provider=None,
):
    ranges = month_start_end_ranges(start_date=start_timestamp, end_date=end_timestamp)

    month_stats = {}
    for month_range in ranges:
        start_timestamp = month_range[0]
        end_timestamp = month_range[1]
        logger.info(f"calculate range [{start_timestamp}, {end_timestamp}]")
        stats = get_performance_stats(
            entity_type=entity_type,
            start_timestamp=start_timestamp,
            end_timestamp=end_timestamp,
            adjust_type=adjust_type,
            data_provider=data_provider,
        )
        if stats:
            month_stats[f"{to_time_str(start_timestamp)}"] = stats

    return pd.DataFrame.from_dict(data=month_stats, orient="index")


def get_performance_stats(
    entity_type="stock",
    start_timestamp=None,
    end_timestamp=None,
    adjust_type: Union[AdjustType, str] = None,
    data_provider=None,
    changes=((-1, -0.5), (-0.5, -0.2), (-0.2, 0), (0, 0.2), (0.2, 0.5), (0.5, 1), (1, 1000)),
):
    if not adjust_type:
        adjust_type = default_adjust_type(entity_type=entity_type)
    data_schema = get_kdata_schema(entity_type=entity_type, adjust_type=adjust_type)

    score_df, _ = get_top_entities(
        data_schema=data_schema,
        column="close",
        start_timestamp=start_timestamp,
        end_timestamp=end_timestamp,
        pct=1,
        method=WindowMethod.change,
        return_type=TopType.positive,
        data_provider=data_provider,
    )

    if pd_is_not_null(score_df):
        result = {}
        for change in changes:
            range_start = change[0]
            range_end = change[1]
            key = f"pct_{range_start}_{range_end}"
            df = score_df[(score_df["score"] >= range_start) & (score_df["score"] < range_end)]
            result[key] = len(df)
        return result


def get_top_volume_entities(
    entity_type="stock",
    entity_ids=None,
    start_timestamp=None,
    end_timestamp=None,
    pct=0.1,
    return_type=TopType.positive,
    adjust_type: Union[AdjustType, str] = None,
    method=WindowMethod.avg,
    data_provider=None,
    threshold=None,
):
    if not adjust_type:
        adjust_type = default_adjust_type(entity_type=entity_type)

    data_schema = get_kdata_schema(entity_type=entity_type, adjust_type=adjust_type)

    filters = []
    if entity_ids:
        filters.append(data_schema.entity_id.in_(entity_ids))
    if threshold:
        filters.append(data_schema.turnover >= threshold)

    result, _ = get_top_entities(
        data_schema=data_schema,
        start_timestamp=start_timestamp,
        end_timestamp=end_timestamp,
        column="turnover",
        pct=pct,
        method=method,
        return_type=return_type,
        kdata_filters=filters,
        data_provider=data_provider,
    )
    return result


def get_top_turnover_rate_entities(
    entity_type="stock",
    entity_ids=None,
    start_timestamp=None,
    end_timestamp=None,
    pct=0.1,
    return_type=TopType.positive,
    adjust_type: Union[AdjustType, str] = None,
    method=WindowMethod.avg,
    data_provider=None,
    threshold=None,
):
    if not adjust_type:
        adjust_type = default_adjust_type(entity_type=entity_type)

    data_schema = get_kdata_schema(entity_type=entity_type, adjust_type=adjust_type)

    filters = []
    if entity_ids:
        filters.append(data_schema.entity_id.in_(entity_ids))
    if threshold:
        filters.append(data_schema.turnover_rate >= threshold)

    result, _ = get_top_entities(
        data_schema=data_schema,
        start_timestamp=start_timestamp,
        end_timestamp=end_timestamp,
        column="turnover_rate",
        pct=pct,
        method=method,
        return_type=return_type,
        kdata_filters=filters,
        data_provider=data_provider,
    )
    return result


def get_top_entities(
    data_schema: Mixin,
    column: str,
    start_timestamp=None,
    end_timestamp=None,
    pct=0.1,
    method: WindowMethod = WindowMethod.change,
    return_type: TopType = None,
    kdata_filters=None,
    show_name=False,
    data_provider=None,
):
    """
    get top entities in specific domain between time range

    :param data_schema: schema in domain
    :param column: schema column
    :param start_timestamp:
    :param end_timestamp:
    :param pct: range (0,1]
    :param method:
    :param return_type:
    :param entity_filters:
    :param kdata_filters:
    :param show_name: show entity name
    :return:
    """
    if type(method) == str:
        method = WindowMethod(method)

    if type(return_type) == str:
        return_type = TopType(return_type)

    if show_name:
        columns = ["entity_id", column, "name"]
    else:
        columns = ["entity_id", column]

    all_df = data_schema.query_data(
        start_timestamp=start_timestamp,
        end_timestamp=end_timestamp,
        columns=columns,
        filters=kdata_filters,
        provider=data_provider,
    )
    if not pd_is_not_null(all_df):
        return None, None
    g = all_df.groupby("entity_id")
    tops = {}
    names = {}
    for entity_id, df in g:
        if method == WindowMethod.change:
            start = df[column].iloc[0]
            end = df[column].iloc[-1]
            if start != 0:
                change = (end - start) / abs(start)
            else:
                change = 0
            tops[entity_id] = change
        elif method == WindowMethod.avg:
            tops[entity_id] = df[column].mean()
        elif method == WindowMethod.sum:
            tops[entity_id] = df[column].sum()

        if show_name:
            names[entity_id] = df["name"].iloc[0]

    positive_df = None
    negative_df = None
    top_index = int(len(tops) * pct)
    if return_type is None or return_type == TopType.positive:
        # from big to small
        positive_tops = {k: v for k, v in sorted(tops.items(), key=lambda item: item[1], reverse=True)}
        positive_tops = dict(itertools.islice(positive_tops.items(), top_index))
        positive_df = pd.DataFrame.from_dict(positive_tops, orient="index")

        col = "score"
        positive_df.columns = [col]
        positive_df.sort_values(by=col, ascending=False)
    if return_type is None or return_type == TopType.negative:
        # from small to big
        negative_tops = {k: v for k, v in sorted(tops.items(), key=lambda item: item[1])}
        negative_tops = dict(itertools.islice(negative_tops.items(), top_index))
        negative_df = pd.DataFrame.from_dict(negative_tops, orient="index")

        col = "score"
        negative_df.columns = [col]
        negative_df.sort_values(by=col)

    if names:
        if pd_is_not_null(positive_df):
            positive_df["name"] = positive_df.index.map(lambda x: names[x])
        if pd_is_not_null(negative_df):
            negative_df["name"] = negative_df.index.map(lambda x: names[x])
    return positive_df, negative_df


def show_month_performance():
    dfs = []
    for timestamp, df in get_top_performance_by_month(start_timestamp="2005-01-01", list_days=250):
        if pd_is_not_null(df):
            df = df.reset_index(drop=True)
            df["entity_id"] = "stock_cn_performance"
            df["timestamp"] = timestamp
            dfs.append(df)

    all_df = pd.concat(dfs)
    print(all_df)

    drawer = Drawer(main_df=all_df)
    drawer.draw_scatter(show=True)


def show_industry_composition(entity_ids, timestamp):
    block_df = Block.query_data(provider="eastmoney", filters=[Block.category == "industry"], index="entity_id")
    block_ids = block_df.index.tolist()

    block_df = BlockStock.query_data(entity_ids=block_ids, filters=[BlockStock.stock_id.in_(entity_ids)])

    s = block_df["name"].value_counts()

    cycle_df = pd.DataFrame(columns=s.index, data=[s.tolist()])
    cycle_df["entity_id"] = "stock_cn_industry"
    cycle_df["timestamp"] = timestamp
    drawer = Drawer(main_df=cycle_df)
    drawer.draw_pie(show=True)


def get_change_ratio(
    entity_type="stock",
    start_timestamp=None,
    end_timestamp=None,
    adjust_type: Union[AdjustType, str] = None,
    provider="em",
):
    def cal_ratio(df):
        positive = df[df["direction"]]
        other = df[~df["direction"]]
        return len(positive) / len(other)

    if not adjust_type:
        adjust_type = default_adjust_type(entity_type=entity_type)
    data_schema = get_kdata_schema(entity_type=entity_type, adjust_type=adjust_type)
    kdata_df = data_schema.query_data(provider=provider, start_timestamp=start_timestamp, end_timestamp=end_timestamp)
    kdata_df["direction"] = kdata_df["change_pct"] > 0
    ratio_df = kdata_df.groupby("timestamp").apply(lambda df: cal_ratio(df))
    return ratio_df


if __name__ == "__main__":
    print(get_top_performance_entities_by_periods(entity_provider="em", data_provider="em"))


# the __all__ is generated
__all__ = [
    "WindowMethod",
    "TopType",
    "get_top_performance_by_month",
    "get_top_performance_entities_by_periods",
    "get_top_performance_entities",
    "get_top_fund_holding_stocks",
    "get_performance",
    "get_performance_stats_by_month",
    "get_performance_stats",
    "get_top_volume_entities",
    "get_top_turnover_rate_entities",
    "get_top_entities",
    "show_month_performance",
    "show_industry_composition",
    "get_change_ratio",
]
