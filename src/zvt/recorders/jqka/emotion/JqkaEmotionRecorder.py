# -*- coding: utf-8 -*-
import re
from typing import List

import pandas as pd

from zvt.api.utils import china_stock_code_to_id
from zvt.contract.api import df_to_db
from zvt.contract.recorder import TimestampsDataRecorder
from zvt.domain import Stock
from zvt.domain.emotion.emotion import LimitUpInfo, LimitDownInfo, Emotion
from zvt.recorders.jqka import jqka_api
from zvt.utils.time_utils import to_time_str, date_time_by_interval, current_date, to_pd_timestamp


def _get_high_days_count(high_days_str: str):
    if not high_days_str or (high_days_str == "首板"):
        return 1
    pattern = r"\d+"
    result = re.findall(pattern, high_days_str)
    return int(result[-1])


class JqkaLimitUpRecorder(TimestampsDataRecorder):
    entity_provider = "em"
    entity_schema = Stock

    provider = "jqka"
    data_schema = LimitUpInfo

    def init_entities(self):
        # fake entity to for trigger run
        self.entities = [Stock(id="stock_sz_000001")]

    def init_timestamps(self, entity_item) -> List[pd.Timestamp]:
        latest_infos = LimitUpInfo.query_data(
            provider=self.provider, order=LimitUpInfo.timestamp.desc(), limit=1, return_type="domain"
        )
        if latest_infos:
            start_date = latest_infos[0].timestamp
        else:
            # 最近一年半的数据
            start_date = date_time_by_interval(current_date(), -365 - 366 / 2)
        return pd.date_range(start=start_date, end=pd.Timestamp.now(), freq="B").tolist()

    def record(self, entity, start, end, size, timestamps):
        for timestamp in timestamps:
            the_date = to_time_str(timestamp)
            self.logger.info(f"record {self.data_schema} to {the_date}")
            limit_ups = jqka_api.get_limit_up(date=the_date)
            if limit_ups:
                records = []
                for data in limit_ups:
                    entity_id = china_stock_code_to_id(code=data["code"])
                    record = {
                        "id": "{}_{}".format(entity_id, the_date),
                        "entity_id": entity_id,
                        "timestamp": to_pd_timestamp(the_date),
                        "code": data["code"],
                        "name": data["name"],
                        "is_new": data["is_new"],
                        "is_again_limit": data["is_again_limit"],
                        "open_count": data["open_num"] if data["open_num"] else 0,
                        "first_limit_up_time": pd.Timestamp.fromtimestamp(int(data["first_limit_up_time"])),
                        "last_limit_up_time": pd.Timestamp.fromtimestamp(int(data["last_limit_up_time"])),
                        "limit_up_type": data["limit_up_type"],
                        "order_amount": data["order_amount"],
                        "success_rate": data["limit_up_suc_rate"],
                        "currency_value": data["currency_value"],
                        "change_pct": data["change_rate"] / 100,
                        "turnover_rate": data["turnover_rate"] / 100,
                        "reason": data["reason_type"],
                        "high_days": data["high_days"],
                        "high_days_count": _get_high_days_count(data["high_days"]),
                    }
                    records.append(record)
                df = pd.DataFrame.from_records(records)
                df_to_db(
                    data_schema=self.data_schema,
                    df=df,
                    provider=self.provider,
                    force_update=True,
                    drop_duplicates=True,
                )


class JqkaLimitDownRecorder(TimestampsDataRecorder):
    entity_provider = "em"
    entity_schema = Stock

    provider = "jqka"
    data_schema = LimitDownInfo

    def init_entities(self):
        # fake entity to for trigger run
        self.entities = [Stock(id="stock_sz_000001")]

    def init_timestamps(self, entity_item) -> List[pd.Timestamp]:
        latest_infos = LimitDownInfo.query_data(
            provider=self.provider, order=LimitDownInfo.timestamp.desc(), limit=1, return_type="domain"
        )
        if latest_infos:
            start_date = latest_infos[0].timestamp
        else:
            # 最近一年半的数据
            start_date = date_time_by_interval(current_date(), -365 - 366 / 2)
        return pd.date_range(start=start_date, end=pd.Timestamp.now(), freq="B").tolist()

    def record(self, entity, start, end, size, timestamps):
        for timestamp in timestamps:
            the_date = to_time_str(timestamp)
            self.logger.info(f"record {self.data_schema} to {the_date}")
            limit_downs = jqka_api.get_limit_down(date=the_date)
            if limit_downs:
                records = []
                for data in limit_downs:
                    entity_id = china_stock_code_to_id(code=data["code"])
                    record = {
                        "id": "{}_{}".format(entity_id, the_date),
                        "entity_id": entity_id,
                        "timestamp": to_pd_timestamp(the_date),
                        "code": data["code"],
                        "name": data["name"],
                        "is_new": data["is_new"],
                        "is_again_limit": data["is_again_limit"],
                        "currency_value": data["currency_value"],
                        "change_pct": data["change_rate"] / 100,
                        "turnover_rate": data["turnover_rate"] / 100,
                    }
                    records.append(record)
                df = pd.DataFrame.from_records(records)
                df_to_db(
                    data_schema=self.data_schema,
                    df=df,
                    provider=self.provider,
                    force_update=True,
                    drop_duplicates=True,
                )


def _cal_power_and_max_height(continuous_limit_up: dict):
    max_height = 0
    power = 0
    for item in continuous_limit_up:
        if max_height < item["height"]:
            max_height = item["height"]
        power = power + item["height"] * item["number"]
    return max_height, power


class JqkaEmotionRecorder(TimestampsDataRecorder):
    entity_provider = "em"
    entity_schema = Stock

    provider = "jqka"
    data_schema = Emotion

    def init_entities(self):
        # fake entity to for trigger run
        self.entities = [Stock(id="stock_sz_000001")]

    def init_timestamps(self, entity_item) -> List[pd.Timestamp]:
        latest_infos = Emotion.query_data(
            provider=self.provider, order=Emotion.timestamp.desc(), limit=1, return_type="domain"
        )
        if latest_infos:
            start_date = latest_infos[0].timestamp
        else:
            # 最近一年的数据
            start_date = date_time_by_interval(current_date(), -365)
        return pd.date_range(start=start_date, end=pd.Timestamp.now(), freq="B").tolist()

    def record(self, entity, start, end, size, timestamps):
        for timestamp in timestamps:
            the_date = to_time_str(timestamp)
            self.logger.info(f"record {self.data_schema} to {the_date}")
            limit_stats = jqka_api.get_limit_stats(date=the_date)
            continuous_limit_up = jqka_api.get_continuous_limit_up(date=the_date)
            max_height, continuous_power = _cal_power_and_max_height(continuous_limit_up=continuous_limit_up)

            if limit_stats:
                # 大盘
                entity_id = "stock_sh_000001"
                record = {
                    "id": "{}_{}".format(entity_id, the_date),
                    "entity_id": entity_id,
                    "timestamp": to_pd_timestamp(the_date),
                    "limit_up_count": limit_stats["limit_up_count"]["today"]["num"],
                    "limit_up_open_count": limit_stats["limit_up_count"]["today"]["open_num"],
                    "limit_up_success_rate": limit_stats["limit_up_count"]["today"]["rate"],
                    "limit_down_count": limit_stats["limit_down_count"]["today"]["num"],
                    "limit_down_open_count": limit_stats["limit_down_count"]["today"]["open_num"],
                    "limit_down_success_rate": limit_stats["limit_down_count"]["today"]["rate"],
                    "max_height": max_height,
                    "continuous_power": continuous_power,
                }
                df = pd.DataFrame.from_records([record])
                df_to_db(
                    data_schema=self.data_schema,
                    df=df,
                    provider=self.provider,
                    force_update=True,
                    drop_duplicates=True,
                )


if __name__ == "__main__":
    JqkaLimitUpRecorder().run()


# the __all__ is generated
__all__ = ["JqkaLimitUpRecorder", "JqkaLimitDownRecorder", "JqkaEmotionRecorder"]
