# -*- coding: utf-8 -*-
import json
import logging
from enum import Enum
from typing import List

import pandas as pd

from zvt.contract.data_type import Bean
from zvt.contract.drawer import Rect
from zvt.factors.algorithm import intersect
from zvt.utils import to_time_str
from zvt.utils.time_utils import TIME_FORMAT_ISO8601

logger = logging.getLogger(__name__)


class Direction(Enum):
    up = "up"
    down = "down"

    def opposite(self):
        if self == Direction.up:
            return Direction.down
        if self == Direction.down:
            return Direction.up


class Fenxing(Bean):
    def __init__(self, state, kdata, index) -> None:
        self.state = state
        self.kdata = kdata
        self.index = index


def fenxing_power(left, middle, right, fenxing="tmp_ding"):
    if fenxing == "tmp_ding":
        a = middle["high"] - middle["close"]
        b = middle["high"] - left["high"]
        c = middle["high"] - right["high"]
        return -(a + b + c) / middle["close"]
    if fenxing == "tmp_di":
        a = abs(middle["low"] - middle["close"])
        b = abs(middle["low"] - left["low"])
        c = abs(middle["low"] - right["low"])
        return (a + b + c) / middle["close"]


def a_include_b(a: pd.Series, b: pd.Series) -> bool:
    """
    kdata a includes kdata b

    :param a:
    :param b:
    :return:
    """
    return (a["high"] >= b["high"]) and (a["low"] <= b["low"])


def get_direction(kdata, pre_kdata, current=Direction.up) -> Direction:
    if is_up(kdata, pre_kdata):
        return Direction.up
    if is_down(kdata, pre_kdata):
        return Direction.down

    return current


def is_up(kdata, pre_kdata):
    return kdata["high"] > pre_kdata["high"]


def is_down(kdata, pre_kdata):
    return kdata["low"] < pre_kdata["low"]


def handle_first_fenxing(one_df, step=11):
    if step >= len(one_df):
        logger.info(f"coult not get fenxing by step {step}, len {len(one_df)}")
        return None, None, None, None

    logger.info(f"try to get first fenxing by step {step}")

    df = one_df.iloc[:step]
    ding_kdata = df[df["high"].max() == df["high"]]
    ding_index = int(ding_kdata.index[-1])

    di_kdata = df[df["low"].min() == df["low"]]
    di_index = int(di_kdata.index[-1])

    # 确定第一个分型
    if abs(ding_index - di_index) >= 4:
        if ding_index > di_index:
            fenxing = "bi_di"
            fenxing_index = di_index
            one_df.loc[di_index, "bi_di"] = True
            # 确定第一个分型后，开始遍历的位置
            start_index = ding_index
            # 目前的笔的方向，up代表寻找 can_ding;down代表寻找can_di
            direction = Direction.up
            interval = ding_index - di_index
        else:
            fenxing = "bi_ding"
            fenxing_index = ding_index
            one_df.loc[ding_index, "bi_ding"] = True
            start_index = di_index
            direction = Direction.down
            interval = di_index - ding_index
        return (
            Fenxing(
                state=fenxing,
                index=fenxing_index,
                kdata={
                    "low": float(one_df.loc[fenxing_index]["low"]),
                    "high": float(one_df.loc[fenxing_index]["high"]),
                },
            ),
            start_index,
            direction,
            interval,
        )
    else:
        logger.info("need add step")
        return handle_first_fenxing(one_df, step=step + 1)


def handle_zhongshu(points: list, acc_df, end_index, zhongshu_col="zhongshu", zhongshu_change_col="zhongshu_change"):
    zhongshu = None
    zhongshu_change = None
    interval = None

    if len(points) == 4:
        x1 = points[0][0]
        x2 = points[3][0]

        interval = points[3][2] - points[0][2]

        if points[0][1] < points[1][1]:
            # 向下段
            range = intersect((points[0][1], points[1][1]), (points[2][1], points[3][1]))
            if range:
                y1, y2 = range
                # 记录中枢
                zhongshu = Rect(x0=x1, x1=x2, y0=y1, y1=y2)
                zhongshu_change = abs(y1 - y2) / y1
                acc_df.loc[end_index, zhongshu_col] = zhongshu
                acc_df.loc[end_index, zhongshu_change_col] = zhongshu_change
                points = points[-1:]
            else:
                points = points[1:]
        else:
            # 向上段
            range = intersect((points[1][1], points[0][1]), (points[3][1], points[2][1]))
            if range:
                y1, y2 = range
                # 记录中枢
                zhongshu = Rect(x0=x1, x1=x2, y0=y1, y1=y2)
                zhongshu_change = abs(y1 - y2) / y1

                acc_df.loc[end_index, zhongshu_col] = zhongshu
                acc_df.loc[end_index, zhongshu_change_col] = zhongshu_change
                points = points[-1:]
            else:
                points = points[1:]
    return points, zhongshu, zhongshu_change, interval


def handle_duan(fenxing_list: List[Fenxing], pre_duan_state="yi"):
    state = fenxing_list[0].state
    # 1笔区间
    bi1_start = fenxing_list[0].kdata
    bi1_end = fenxing_list[1].kdata
    # 3笔区间
    bi3_start = fenxing_list[2].kdata
    bi3_end = fenxing_list[3].kdata

    if state == "bi_ding":
        # 向下段,下-上-下

        # 第一笔区间
        range1 = (bi1_end["low"], bi1_start["high"])
        # 第三笔区间
        range3 = (bi3_end["low"], bi3_start["high"])

        # 1,3有重叠，认为第一个段出现
        if intersect(range1, range3):
            return "down"

    else:
        # 向上段，上-下-上

        # 第一笔区间
        range1 = (bi1_start["low"], bi1_end["high"])
        # 第三笔区间
        range3 = (bi3_start["low"], bi3_end["high"])

        # 1,3有重叠，认为第一个段出现
        if intersect(range1, range3):
            return "up"

    return pre_duan_state


def handle_including(one_df, index, kdata, pre_index, pre_kdata, tmp_direction: Direction):
    # 改kdata
    if a_include_b(kdata, pre_kdata):
        # 长的kdata变短
        if tmp_direction == Direction.up:
            one_df.loc[index, "low"] = pre_kdata["low"]
        else:
            one_df.loc[index, "high"] = pre_kdata["high"]
    # 改pre_kdata
    elif a_include_b(pre_kdata, kdata):
        # 长的pre_kdata变短
        if tmp_direction == Direction.down:
            one_df.loc[pre_index, "low"] = kdata["low"]
        else:
            one_df.loc[pre_index, "high"] = kdata["high"]


class FactorStateEncoder(json.JSONEncoder):
    def default(self, object):
        if isinstance(object, pd.Series):
            return object.to_dict()
        elif isinstance(object, pd.Timestamp):
            return to_time_str(object, fmt=TIME_FORMAT_ISO8601)
        elif isinstance(object, Enum):
            return object.value
        elif isinstance(object, Bean):
            return object.dict()
        else:
            return super().default(object)


def decode_rect(dct):
    return Rect(x0=dct["x0"], y0=dct["y0"], x1=dct["x1"], y1=dct["y1"])


def decode_fenxing(dct):
    return Fenxing(state=dct["state"], kdata=dct["kdata"], index=dct["index"])


# the __all__ is generated
__all__ = [
    "Direction",
    "Fenxing",
    "fenxing_power",
    "a_include_b",
    "get_direction",
    "is_up",
    "is_down",
    "handle_first_fenxing",
    "handle_zhongshu",
    "handle_duan",
    "handle_including",
    "FactorStateEncoder",
    "decode_rect",
    "decode_fenxing",
]
