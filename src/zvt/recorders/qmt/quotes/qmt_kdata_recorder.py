# -*- coding: utf-8 -*-
import pandas as pd

from zvt.api.kdata import get_kdata_schema, get_kdata
from zvt.broker.qmt import qmt_quote
from zvt.contract import IntervalLevel, AdjustType
from zvt.contract.api import df_to_db
from zvt.contract.recorder import FixedCycleDataRecorder
from zvt.contract.utils import evaluate_size_from_timestamp
from zvt.domain import (
    Stock,
    StockKdataCommon,
)
from zvt.utils.pd_utils import pd_is_not_null
from zvt.utils.time_utils import current_date, to_time_str, TIME_FORMAT_DAY, TIME_FORMAT_MINUTE


class BaseQmtKdataRecorder(FixedCycleDataRecorder):
    default_size = 50000
    entity_provider: str = "qmt"

    provider = "qmt"
    download_history_data = False

    def __init__(
            self,
            force_update=True,
            sleeping_time=10,
            exchanges=None,
            entity_id=None,
            entity_ids=None,
            code=None,
            codes=None,
            day_data=False,
            entity_filters=None,
            ignore_failed=True,
            real_time=False,
            fix_duplicate_way="ignore",
            start_timestamp=None,
            end_timestamp=None,
            level=IntervalLevel.LEVEL_1DAY,
            kdata_use_begin_time=False,
            one_day_trading_minutes=24 * 60,
            adjust_type=AdjustType.qfq,
            return_unfinished=False,
            download_history_data=False
    ) -> None:
        level = IntervalLevel(level)
        self.adjust_type = AdjustType(adjust_type)
        self.entity_type = self.entity_schema.__name__.lower()
        self.download_history_data = download_history_data

        self.data_schema = get_kdata_schema(entity_type=self.entity_type, level=level, adjust_type=self.adjust_type)

        super().__init__(
            force_update,
            sleeping_time,
            exchanges,
            entity_id,
            entity_ids,
            code,
            codes,
            day_data,
            entity_filters,
            ignore_failed,
            real_time,
            fix_duplicate_way,
            start_timestamp,
            end_timestamp,
            level,
            kdata_use_begin_time,
            one_day_trading_minutes,
            return_unfinished,
        )
        self.one_day_trading_minutes = 240

    def record(self, entity, start, end, size, timestamps):
        if start and (self.level == IntervalLevel.LEVEL_1DAY):
            start = start.date()

        # 判断是否需要重新计算之前保存的前复权数据
        if start and (self.adjust_type == AdjustType.qfq):
            check_df = qmt_quote.get_kdata(
                entity_id=entity.id,
                start_timestamp=start,
                end_timestamp=start,
                adjust_type=self.adjust_type,
                level=self.level,
                download_history=self.download_history_data,
            )
            if pd_is_not_null(check_df):
                current_df = get_kdata(
                    entity_id=entity.id,
                    provider=self.provider,
                    start_timestamp=start,
                    end_timestamp=start,
                    limit=1,
                    level=self.level,
                    adjust_type=self.adjust_type,
                )
                if pd_is_not_null(current_df):
                    old = current_df.iloc[0, :]["close"]
                    new = check_df["close"][0]
                    # 相同时间的close不同，表明前复权需要重新计算
                    if round(old, 2) != round(new, 2):
                        # 删掉重新获取
                        self.session.query(self.data_schema).filter(self.data_schema.entity_id == entity.id).delete()
                        start = "2005-01-01"

        if not start:
            start = "2005-01-01"
        if not end:
            end = current_date()

        # 统一高频数据习惯，减小数据更新次数，分钟K线需要直接多读1根K线，以兼容start_timestamp=9:30, end_timestamp=15:00的情况
        if self.level == IntervalLevel.LEVEL_1MIN:
            end += pd.Timedelta(seconds=1)

        df = qmt_quote.get_kdata(
            entity_id=entity.id,
            start_timestamp=start,
            end_timestamp=end,
            adjust_type=self.adjust_type,
            level=self.level,
            download_history=self.download_history_data,
        )
        time_str_fmt = TIME_FORMAT_DAY if self.level == IntervalLevel.LEVEL_1DAY else TIME_FORMAT_MINUTE
        if pd_is_not_null(df):
            df["entity_id"] = entity.id
            df["timestamp"] = pd.to_datetime(df.index)
            df["id"] = df.apply(lambda row: f"{row['entity_id']}_{to_time_str(row['timestamp'], fmt=time_str_fmt)}",
                                axis=1)
            df["provider"] = "qmt"
            df["level"] = self.level.value
            df["code"] = entity.code
            df["name"] = entity.name
            df.rename(columns={"amount": "turnover"}, inplace=True)
            df["change_pct"] = (df["close"] - df["preClose"]) / df["preClose"]
            df_to_db(df=df, data_schema=self.data_schema, provider=self.provider, force_update=self.force_update)

        else:
            self.logger.info(f"no kdata for {entity.id}")

    def evaluate_start_end_size_timestamps(self, entity):
        if self.download_history_data and self.start_timestamp and self.end_timestamp:
            # 历史数据可能碎片化，允许按照实际start和end之间有没有写满数据
            expected_size = evaluate_size_from_timestamp(start_timestamp=self.start_timestamp,
                                                         end_timestamp=self.end_timestamp, level=self.level,
                                                         one_day_trading_minutes=self.one_day_trading_minutes)

            recorded_size = self.session.query(self.data_schema).filter(
                self.data_schema.entity_id == entity.id,
                self.data_schema.timestamp >= self.start_timestamp,
                self.data_schema.timestamp <= self.end_timestamp
            ).count()

            if expected_size != recorded_size:
                # print(f"expected_size: {expected_size}, recorded_size: {recorded_size}")
                return self.start_timestamp, self.end_timestamp, self.default_size, None

        start_timestamp, end_timestamp, size, timestamps = super().evaluate_start_end_size_timestamps(entity)
        # start_timestamp is the last updated timestamp
        if self.end_timestamp is not None:
            if start_timestamp >= self.end_timestamp:
                return start_timestamp, end_timestamp, 0, None
            else:
                size = evaluate_size_from_timestamp(
                    start_timestamp=start_timestamp,
                    level=self.level,
                    one_day_trading_minutes=self.one_day_trading_minutes,
                    end_timestamp=self.end_timestamp,
                )
                return start_timestamp, self.end_timestamp, size, timestamps

        return start_timestamp, end_timestamp, size, timestamps


class QMTStockKdataRecorder(BaseQmtKdataRecorder):
    entity_schema = Stock
    data_schema = StockKdataCommon


if __name__ == "__main__":
    # Stock.record_data(provider="qmt")
    QMTStockKdataRecorder(entity_id="stock_sz_002231", adjust_type=AdjustType.qfq, level=IntervalLevel.LEVEL_1MIN).run()

# the __all__ is generated
__all__ = ["BaseQmtKdataRecorder", "QMTStockKdataRecorder"]
