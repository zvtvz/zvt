# -*- coding: utf-8 -*-

from zvt.api.kdata import default_adjust_type, get_latest_kdata_date, get_kdata_schema
from zvt.contract import IntervalLevel, AdjustType
from zvt.utils import to_pd_timestamp

# 500亿
BIG_CAP = 50000000000
# 150亿
MIDDLE_CAP = 15000000000
# 40亿
SMALL_CAP = 4000000000


def get_entity_list_by_cap(timestamp, cap_start, cap_end, entity_type="stock", provider=None, adjust_type=None):
    if not adjust_type:
        adjust_type = default_adjust_type(entity_type=entity_type)

    kdata_schema = get_kdata_schema(entity_type, level=IntervalLevel.LEVEL_1DAY, adjust_type=adjust_type)
    df = kdata_schema.query_data(
        provider=provider,
        filters=[kdata_schema.timestamp == to_pd_timestamp(timestamp)],
        index="entity_id",
    )
    df["cap"] = df["turnover"] / df["turnover_rate"]
    df_result = df.copy()
    if cap_start:
        df_result = df_result.loc[(df["cap"] >= cap_start)]
    if cap_end:
        df_result = df_result.loc[(df["cap"] <= cap_end)]
    return df_result.index.tolist()


def get_big_cap_stock(timestamp, provider="em"):
    return get_entity_list_by_cap(
        timestamp=timestamp, cap_start=BIG_CAP, cap_end=None, entity_type="stock", provider=provider
    )


def get_middle_cap_stock(timestamp, provider="em"):
    return get_entity_list_by_cap(
        timestamp=timestamp, cap_start=MIDDLE_CAP, cap_end=BIG_CAP, entity_type="stock", provider=provider
    )


def get_small_cap_stock(timestamp, provider="em"):
    return get_entity_list_by_cap(
        timestamp=timestamp, cap_start=SMALL_CAP, cap_end=MIDDLE_CAP, entity_type="stock", provider=provider
    )


def get_mini_cap_stock(timestamp, provider="em"):
    return get_entity_list_by_cap(
        timestamp=timestamp, cap_start=None, cap_end=SMALL_CAP, entity_type="stock", provider=provider
    )


def get_mini_and_small_stock(timestamp, provider="em"):
    return get_entity_list_by_cap(
        timestamp=timestamp, cap_start=None, cap_end=MIDDLE_CAP, entity_type="stock", provider=provider
    )


def get_middle_and_big_stock(timestamp, provider="em"):
    return get_entity_list_by_cap(
        timestamp=timestamp, cap_start=MIDDLE_CAP, cap_end=None, entity_type="stock", provider=provider
    )


if __name__ == "__main__":
    target_date = get_latest_kdata_date(provider="em", entity_type="stock", adjust_type=AdjustType.hfq)
    big = get_big_cap_stock(timestamp=target_date)
    print(len(big))
    print(big)
    middle = get_middle_cap_stock(timestamp=target_date)
    print(len(middle))
    print(middle)
    small = get_small_cap_stock(timestamp=target_date)
    print(len(small))
    print(small)
    mini = get_mini_cap_stock(timestamp=target_date)
    print(len(mini))
    print(mini)
# the __all__ is generated
__all__ = [
    "get_entity_list_by_cap",
    "get_big_cap_stock",
    "get_middle_cap_stock",
    "get_small_cap_stock",
    "get_mini_cap_stock",
    "get_mini_and_small_stock",
    "get_middle_and_big_stock",
]
