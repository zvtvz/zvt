# -*- coding: utf-8 -*-
import enum
import itertools
import logging
from typing import Union

import pandas as pd

from zvt.api.kdata import get_kdata_schema, default_adjust_type
from zvt.api.utils import get_recent_report_date
from zvt.contract import Mixin, AdjustType
from zvt.contract.api import decode_entity_id, get_entity_schema, get_entity_ids
from zvt.contract.drawer import Drawer
from zvt.domain import FundStock, StockValuation, BlockStock, Block
from zvt.utils import now_pd_timestamp, next_date, pd_is_not_null
from zvt.utils.time_utils import month_start_end_ranges, pre_month_end_date

logger = logging.getLogger(__name__)


class WindowMethod(enum.Enum):
    change = "change"
    avg = "avg"
    sum = "sum"


class TopType(enum.Enum):
    positive = "positive"
    negative = "negative"


def got_top_performance_by_month(
    entity_type="stock",
    start_timestamp="2015-01-01",
    end_timestamp=now_pd_timestamp(),
    list_days=None,
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
        )

        yield (end_timestamp, top)


def get_top_performance_entities(
    entity_type="stock",
    start_timestamp=None,
    end_timestamp=None,
    pct=0.1,
    return_type=None,
    adjust_type: Union[AdjustType, str] = None,
    filters=None,
    show_name=False,
    list_days=None,
    entity_provider=None,
    data_provider=None,
):
    if not adjust_type:
        adjust_type = default_adjust_type(entity_type=entity_type)
    data_schema = get_kdata_schema(entity_type=entity_type, adjust_type=adjust_type)

    if list_days:
        entity_schema = get_entity_schema(entity_type=entity_type)
        list_date = next_date(start_timestamp, -list_days)
        ignore_entities = get_entity_ids(
            provider=entity_provider,
            entity_type=entity_type,
            filters=[entity_schema.list_date >= list_date],
        )
        if ignore_entities:
            logger.info(f"ignore size: {len(ignore_entities)}")
            logger.info(f"ignore entities: {ignore_entities}")
            f = [data_schema.entity_id.notin_(ignore_entities)]
            if filters:
                filters = filters + f
            else:
                filters = f

    return get_top_entities(
        data_schema=data_schema,
        start_timestamp=start_timestamp,
        end_timestamp=end_timestamp,
        column="close",
        pct=pct,
        method=WindowMethod.change,
        return_type=return_type,
        filters=filters,
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
    start_timestamp = next_date(timestamp, -30)
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
        filters=[data_schema.entity_id.in_(entity_ids)],
        data_provider=data_provider,
    )
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
):
    if not adjust_type:
        adjust_type = default_adjust_type(entity_type=entity_type)

    data_schema = get_kdata_schema(entity_type=entity_type, adjust_type=adjust_type)

    filters = None
    if entity_ids:
        filters = [data_schema.entity_id.in_(entity_ids)]

    result, _ = get_top_entities(
        data_schema=data_schema,
        start_timestamp=start_timestamp,
        end_timestamp=end_timestamp,
        column="turnover",
        pct=pct,
        method=method,
        return_type=return_type,
        filters=filters,
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
    filters=None,
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
    :param filters:
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
        filters=filters,
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
            change = (end - start) / start
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
    for timestamp, df in got_top_performance_by_month(start_timestamp="2005-01-01", list_days=250):
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


if __name__ == "__main__":
    # show_month_performance()
    # dfs = []
    for timestamp, df in got_top_performance_by_month(start_timestamp="2012-01-01", list_days=250):
        if pd_is_not_null(df):
            entity_ids = df.index.tolist()
            the_date = pre_month_end_date(timestamp)
            show_industry_composition(entity_ids=entity_ids, timestamp=timestamp)
            # for entity_id in df.index:
            #     from zvt.utils.time_utils import month_end_date, pre_month_start_date
            #
            #     end_date = month_end_date(pre_month_start_date(timestamp))
            #     TechnicalFactor(entity_ids=[entity_id], end_timestamp=end_date).draw(show=True)

# the __all__ is generated
__all__ = [
    "WindowMethod",
    "TopType",
    "got_top_performance_by_month",
    "get_top_performance_entities",
    "get_top_fund_holding_stocks",
    "get_performance",
    "get_top_volume_entities",
    "get_top_entities",
    "show_month_performance",
    "show_industry_composition",
]
