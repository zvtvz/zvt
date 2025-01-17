# -*- coding: utf-8 -*-
import logging
import math
from enum import Enum
from typing import List, Optional
from typing import Union, Type

import pandas as pd

from zvt.contract import IntervalLevel, AdjustType
from zvt.contract import TradableEntity
from zvt.contract.data_type import Bean
from zvt.contract.drawer import Rect
from zvt.contract.factor import Accumulator
from zvt.contract.factor import Transformer
from zvt.domain import Stock
from zvt.factors.algorithm import distance, intersect
from zvt.factors.zen.base_factor import ZenFactor
from zvt.utils.pd_utils import (
    group_by_entity_id,
    normalize_group_compute_result,
    pd_is_not_null,
)

logger = logging.getLogger(__name__)


class ZhongshuRange(Enum):
    # <=0.4
    small = "small"
    # >0.4
    big = "big"

    @classmethod
    def of(cls, change):
        if change <= 0.4:
            return ZhongshuRange.small
        else:
            return ZhongshuRange.big


class ZhongshuLevel(Enum):
    # level <= 3
    level1 = "level1"
    # 3 < level <=7
    level2 = "level2"
    # level > 7
    level3 = "level3"

    @classmethod
    def of(cls, level):
        if level <= 3:
            return ZhongshuLevel.level1
        elif level <= 7:
            return ZhongshuLevel.level2
        else:
            return ZhongshuLevel.level3


class ZhongshuDistance(Enum):
    big_up = "big_up"
    big_down = "big_down"
    small_up = "small_up"
    small_down = "small_down"

    @classmethod
    def of(cls, d):
        if d is None or math.isnan(d) or d == 0:
            zhongshu_distance = None
        elif d <= -0.5:
            zhongshu_distance = ZhongshuDistance.big_down
        elif d < 0:
            zhongshu_distance = ZhongshuDistance.small_down
        elif d <= 0.5:
            zhongshu_distance = ZhongshuDistance.small_up
        else:
            zhongshu_distance = ZhongshuDistance.big_up
        return zhongshu_distance


class Zhongshu(object):
    def __str__(self) -> str:
        if self.zhongshu_distance:
            d = self.zhongshu_distance.value
        else:
            d = None
        return f"{self.zhongshu_range.value},{self.zhongshu_level.value},{d}"

    def __eq__(self, o: object) -> bool:
        if isinstance(o, self.__class__):
            return (
                self.zhongshu_range == o.zhongshu_range
                and self.zhongshu_level == o.zhongshu_level
                and self.zhongshu_distance == o.zhongshu_distance
            )
        return False

    def __init__(
        self,
        zhongshu_range: ZhongshuRange,
        zhongshu_level: ZhongshuLevel,
        zhongshu_distance: ZhongshuDistance,
    ) -> None:
        self.zhongshu_range = zhongshu_range
        self.zhongshu_level = zhongshu_level
        self.zhongshu_distance = zhongshu_distance


def category_zen_state():
    all_states = []

    for zhongshu_range in ZhongshuRange:
        for zhongshu_level in ZhongshuLevel:
            for distance in ZhongshuDistance:
                pass


class ZenState(Bean):
    def __eq__(self, o: object) -> bool:
        if isinstance(o, self.__class__):
            return self.zhongshu_list == o.zhongshu_list

    def __str__(self) -> str:
        return ",".join([f"{elem}" for elem in self.zhongshu_list])

    def __init__(self, zhongshu_state_list: List) -> None:
        self.zhongshu_list: List[Zhongshu] = []
        self.zhongshu_state_list = zhongshu_state_list

        pre_range = None
        for zhongshu_state in zhongshu_state_list:
            current_range = (zhongshu_state[0], zhongshu_state[1])
            d = None
            if pre_range is None:
                pre_range = current_range
            else:
                d = distance(pre_range, current_range)
                pre_range = current_range
            change = zhongshu_state[2]
            level = zhongshu_state[3]

            zhongshu_range = ZhongshuRange.of(change=change)
            zhongshu_level = ZhongshuLevel.of(level=level)
            zhongshu_distance = ZhongshuDistance.of(d=d)

            zhongshu = Zhongshu(
                zhongshu_range=zhongshu_range,
                zhongshu_level=zhongshu_level,
                zhongshu_distance=zhongshu_distance,
            )

            self.zhongshu_list.append(zhongshu)


def cal_distance(s):
    d_list = []
    current_range = None
    print(s)
    for idx, row in s.items():
        d = None
        if row is not None:
            if current_range is None:
                current_range = row
            else:
                d = distance((current_range.y0, current_range.y1), (row.y0, row.y1))
                current_range = row
        d_list.append(d)
    return pd.Series(index=s.index, data=d_list)


def cal_zen_state(s):
    zen_states = []
    zhongshu_state_list = []
    current_zhongshu_state = None
    for idx, row in s.items():
        # row
        # 0 current_merge_zhongshu_y0
        # 1 current_merge_zhongshu_y1
        # 2 current_merge_zhongshu_change
        # 3 current_merge_zhongshu_level
        # 4 current_merge_zhongshu_interval
        if row[0] is not None and not math.isnan(row[0]):
            if current_zhongshu_state != row:
                # 相同的中枢，保留最近的(包含关系时产生)
                if current_zhongshu_state != None and intersect(
                    (current_zhongshu_state[0], current_zhongshu_state[1]),
                    (row[0], row[1]),
                ):
                    zhongshu_state_list = zhongshu_state_list[:-1]

                # 最多保留最近5个
                zhongshu_state_list = zhongshu_state_list[-4:] + [row]
                current_zhongshu_state = row

        if len(zhongshu_state_list) == 5:
            zen_states.append(ZenState(zhongshu_state_list))
        else:
            zen_states.append(None)
    return pd.Series(index=s.index, data=zen_states)


def good_state(zen_state: ZenState):
    if zen_state:
        zhongshu0 = zen_state.zhongshu_list[0]
        zhongshu1 = zen_state.zhongshu_list[1]
        zhongshu2 = zen_state.zhongshu_list[2]
        zhongshu3 = zen_state.zhongshu_list[3]
        zhongshu4 = zen_state.zhongshu_list[4]

        # 没大涨过
        if ZhongshuDistance.big_up not in (
            zhongshu1.zhongshu_distance,
            zhongshu2.zhongshu_distance,
            zhongshu3.zhongshu_distance,
            zhongshu4.zhongshu_distance,
        ):
            if ZhongshuRange.big not in (
                zhongshu3.zhongshu_range,
                zhongshu4.zhongshu_range,
            ):
                # 最近一个窄幅震荡
                if ZhongshuRange.small == zhongshu4.zhongshu_range and ZhongshuLevel.level1 != zhongshu4.zhongshu_level:
                    return True

    return False


def trending_state(zen_state: ZenState):
    if zen_state:
        zhongshu0 = zen_state.zhongshu_list[0]
        zhongshu1 = zen_state.zhongshu_list[1]
        zhongshu2 = zen_state.zhongshu_list[2]
        zhongshu3 = zen_state.zhongshu_list[3]
        zhongshu4 = zen_state.zhongshu_list[4]

        # 没大涨过
        if ZhongshuDistance.big_up not in (
            zhongshu1.zhongshu_distance,
            zhongshu2.zhongshu_distance,
            zhongshu3.zhongshu_distance,
        ):
            if ZhongshuRange.big not in (
                zhongshu3.zhongshu_range,
                zhongshu4.zhongshu_range,
            ):
                # 最近一个窄幅震荡
                if ZhongshuRange.small == zhongshu4.zhongshu_range and ZhongshuLevel.level1 == zhongshu4.zhongshu_level:
                    return True

    return False


class TrendingFactor(ZenFactor):
    def __init__(
        self,
        entity_schema: Type[TradableEntity] = Stock,
        provider: str = None,
        entity_provider: str = None,
        entity_ids: List[str] = None,
        exchanges: List[str] = None,
        codes: List[str] = None,
        start_timestamp: Union[str, pd.Timestamp] = None,
        end_timestamp: Union[str, pd.Timestamp] = None,
        columns: List = None,
        filters: List = None,
        order: object = None,
        limit: int = None,
        level: Union[str, IntervalLevel] = IntervalLevel.LEVEL_1DAY,
        category_field: str = "entity_id",
        time_field: str = "timestamp",
        keep_window: int = None,
        keep_all_timestamp: bool = False,
        fill_method: str = "ffill",
        effective_number: int = None,
        transformer: Transformer = None,
        accumulator: Accumulator = None,
        need_persist: bool = False,
        only_compute_factor: bool = False,
        factor_name: str = None,
        clear_state: bool = False,
        only_load_factor: bool = True,
        adjust_type: Union[AdjustType, str] = None,
    ) -> None:
        super().__init__(
            entity_schema,
            provider,
            entity_provider,
            entity_ids,
            exchanges,
            codes,
            start_timestamp,
            end_timestamp,
            columns,
            filters,
            order,
            limit,
            level,
            category_field,
            time_field,
            keep_window,
            keep_all_timestamp,
            fill_method,
            effective_number,
            transformer,
            accumulator,
            need_persist,
            only_compute_factor,
            factor_name,
            clear_state,
            only_load_factor,
            adjust_type,
        )

    def compute_result(self):
        super().compute_result()
        if pd_is_not_null(self.factor_df):
            df = self.factor_df.apply(
                lambda x: (
                    x["current_merge_zhongshu_y0"],
                    x["current_merge_zhongshu_y1"],
                    x["current_merge_zhongshu_change"],
                    x["current_merge_zhongshu_level"],
                    x["current_merge_zhongshu_interval"],
                ),
                axis=1,
            )

            state_df = group_by_entity_id(df).apply(cal_zen_state)
            print(self.factor_df)
            print(state_df)
            self.factor_df["zen_state"] = normalize_group_compute_result(state_df)
            self.factor_df["good_state"] = self.factor_df["zen_state"].apply(good_state)

            s = self.factor_df["good_state"]
            self.result_df = s.to_frame(name="filter_result")


class ShakingFactor(ZenFactor):
    # 震荡区间
    shaking_range = 0.5

    def __init__(
        self,
        entity_schema: Type[TradableEntity] = Stock,
        provider: str = None,
        entity_provider: str = None,
        entity_ids: List[str] = None,
        exchanges: List[str] = None,
        codes: List[str] = None,
        start_timestamp: Union[str, pd.Timestamp] = None,
        end_timestamp: Union[str, pd.Timestamp] = None,
        columns: List = None,
        filters: List = None,
        order: object = None,
        limit: int = None,
        level: Union[str, IntervalLevel] = IntervalLevel.LEVEL_1DAY,
        category_field: str = "entity_id",
        time_field: str = "timestamp",
        keep_window: int = None,
        keep_all_timestamp: bool = False,
        fill_method: str = "ffill",
        effective_number: int = None,
        transformer: Transformer = None,
        accumulator: Accumulator = None,
        need_persist: bool = False,
        only_compute_factor: bool = False,
        factor_name: str = None,
        clear_state: bool = False,
        only_load_factor: bool = True,
        adjust_type: Union[AdjustType, str] = None,
    ) -> None:
        super().__init__(
            entity_schema,
            provider,
            entity_provider,
            entity_ids,
            exchanges,
            codes,
            start_timestamp,
            end_timestamp,
            columns,
            filters,
            order,
            limit,
            level,
            category_field,
            time_field,
            keep_window,
            keep_all_timestamp,
            fill_method,
            effective_number,
            transformer,
            accumulator,
            need_persist,
            only_compute_factor,
            factor_name,
            clear_state,
            only_load_factor,
            adjust_type,
        )

    def drawer_sub_df_list(self) -> Optional[List[pd.DataFrame]]:
        df1 = self.factor_df[["current_merge_zhongshu_y1"]].dropna()
        df2 = self.factor_df[["current_merge_zhongshu_y0"]].dropna()
        return [df1, df2]

    def drawer_rects(self) -> List[Rect]:
        return super().drawer_rects()

    def compute_result(self):
        super().compute_result()
        # 窄幅震荡
        s1 = self.factor_df["current_merge_zhongshu_change"] <= self.shaking_range
        # 中枢级别
        s2 = self.factor_df["current_merge_zhongshu_level"] >= 2
        s3 = self.factor_df["current_merge_zhongshu_interval"] >= 120

        # 中枢上缘
        s4 = self.factor_df["close"] <= 1.1 * self.factor_df["current_merge_zhongshu_y1"]
        s5 = self.factor_df["close"] >= 0.9 * self.factor_df["current_merge_zhongshu_y1"]

        # 中枢下缘
        s6 = self.factor_df["close"] <= 1.1 * self.factor_df["current_merge_zhongshu_y0"]
        s7 = self.factor_df["close"] >= 0.9 * self.factor_df["current_merge_zhongshu_y0"]

        s = s1 & s2 & s3 & ((s4 & s5) | (s6 & s7))
        # s = s.groupby(level=0).apply(drop_continue_duplicate)
        if s.index.nlevels == 3:
            s = s.reset_index(level=0, drop=True)

        self.result_df = s.to_frame(name="filter_result")
        print(self.result_df)


if __name__ == "__main__":
    entity_ids = ["stock_sz_000338"]

    f = ZenFactor(
        provider="em",
        entity_schema=Stock,
        entity_ids=entity_ids,
        need_persist=True,
    )
    f.draw(show=True)


# the __all__ is generated
__all__ = [
    "ZhongshuRange",
    "ZhongshuLevel",
    "ZhongshuDistance",
    "Zhongshu",
    "category_zen_state",
    "ZenState",
    "cal_distance",
    "cal_zen_state",
    "good_state",
    "trending_state",
    "TrendingFactor",
    "ShakingFactor",
]
