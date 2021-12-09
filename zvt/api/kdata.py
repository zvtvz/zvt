# -*- coding: utf-8 -*-

from typing import Union

import numpy as np
import pandas as pd

from zvt.contract import IntervalLevel, AdjustType, Mixin
from zvt.contract.api import decode_entity_id, get_schema_by_name
from zvt.utils.pd_utils import pd_is_not_null
from zvt.utils.time_utils import to_time_str, TIME_FORMAT_DAY, TIME_FORMAT_ISO8601


def get_latest_kdata_date(
    entity_type: str,
    provider: str = None,
    level: Union[IntervalLevel, str] = IntervalLevel.LEVEL_1DAY,
    adjust_type: Union[AdjustType, str] = None,
):
    data_schema: Mixin = get_kdata_schema(entity_type, level=level, adjust_type=adjust_type)

    latest_data = data_schema.query_data(
        provider=provider, order=data_schema.timestamp.desc(), limit=1, return_type="domain"
    )
    return latest_data[0].timestamp


def get_kdata_schema(
    entity_type: str,
    level: Union[IntervalLevel, str] = IntervalLevel.LEVEL_1DAY,
    adjust_type: Union[AdjustType, str] = None,
) -> Mixin:
    if type(level) == str:
        level = IntervalLevel(level)
    if type(adjust_type) == str:
        adjust_type = AdjustType(adjust_type)

    # kdata schema rule
    # name:{entity_type.capitalize()}{IntervalLevel.value.capitalize()}Kdata
    if adjust_type and (adjust_type != AdjustType.qfq):
        schema_str = "{}{}{}Kdata".format(
            entity_type.capitalize(),
            level.value.capitalize(),
            adjust_type.value.capitalize(),
        )
    else:
        schema_str = "{}{}Kdata".format(entity_type.capitalize(), level.value.capitalize())
    return get_schema_by_name(schema_str)


def get_kdata(
    entity_id=None,
    entity_ids=None,
    level=IntervalLevel.LEVEL_1DAY.value,
    provider=None,
    columns=None,
    return_type="df",
    start_timestamp=None,
    end_timestamp=None,
    filters=None,
    session=None,
    order=None,
    limit=None,
    index="timestamp",
    adjust_type: AdjustType = None,
):
    assert not entity_id or not entity_ids
    if entity_ids:
        entity_id = entity_ids[0]
    else:
        entity_ids = [entity_id]

    entity_type, exchange, code = decode_entity_id(entity_id)
    data_schema: Mixin = get_kdata_schema(entity_type, level=level, adjust_type=adjust_type)

    return data_schema.query_data(
        entity_ids=entity_ids,
        level=level,
        provider=provider,
        columns=columns,
        return_type=return_type,
        start_timestamp=start_timestamp,
        end_timestamp=end_timestamp,
        filters=filters,
        session=session,
        order=order,
        limit=limit,
        index=index,
    )


def default_adjust_type(entity_type: str) -> AdjustType:
    """
    :type entity_type: entity type, e.g stock, stockhk, stockus
    """
    if entity_type.startswith("stock"):
        return AdjustType.hfq
    return AdjustType.qfq


def generate_kdata_id(entity_id, timestamp, level):
    if level >= IntervalLevel.LEVEL_1DAY:
        return "{}_{}".format(entity_id, to_time_str(timestamp, fmt=TIME_FORMAT_DAY))
    else:
        return "{}_{}".format(entity_id, to_time_str(timestamp, fmt=TIME_FORMAT_ISO8601))


def to_high_level_kdata(kdata_df: pd.DataFrame, to_level: IntervalLevel):
    def to_close(s):
        if pd_is_not_null(s):
            return s[-1]

    def to_open(s):
        if pd_is_not_null(s):
            return s[0]

    def to_high(s):
        return np.max(s)

    def to_low(s):
        return np.min(s)

    def to_sum(s):
        return np.sum(s)

    original_level = kdata_df["level"][0]
    entity_id = kdata_df["entity_id"][0]
    provider = kdata_df["provider"][0]
    name = kdata_df["name"][0]
    code = kdata_df["code"][0]

    entity_type, _, _ = decode_entity_id(entity_id=entity_id)

    assert IntervalLevel(original_level) <= IntervalLevel.LEVEL_1DAY
    assert IntervalLevel(original_level) < IntervalLevel(to_level)

    df: pd.DataFrame = None
    if to_level == IntervalLevel.LEVEL_1WEEK:
        # loffset='-2'　用周五作为时间标签
        if entity_type == "stock":
            df = kdata_df.resample("W", loffset=pd.DateOffset(days=-2)).apply(
                {
                    "close": to_close,
                    "open": to_open,
                    "high": to_high,
                    "low": to_low,
                    "volume": to_sum,
                    "turnover": to_sum,
                }
            )
        else:
            df = kdata_df.resample("W", loffset=pd.DateOffset(days=-2)).apply(
                {
                    "close": to_close,
                    "open": to_open,
                    "high": to_high,
                    "low": to_low,
                    "volume": to_sum,
                    "turnover": to_sum,
                }
            )
    df = df.dropna()
    # id        entity_id  timestamp   provider    code  name level
    df["entity_id"] = entity_id
    df["provider"] = provider
    df["code"] = code
    df["name"] = name

    return df


# the __all__ is generated
__all__ = ["get_kdata_schema", "get_kdata", "generate_kdata_id", "to_high_level_kdata"]
