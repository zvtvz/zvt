# -*- coding: utf-8 -*-
import pandas as pd

from zvt.api.kdata import get_kdata_schema
from zvt.broker.qmt import qmt_quote
from zvt.contract import IntervalLevel, AdjustType
from zvt.contract.api import df_to_db
from zvt.contract.recorder import FixedCycleDataRecorder
from zvt.domain import (
    Stock,
    StockKdataCommon,
)
from zvt.utils.pd_utils import pd_is_not_null
from zvt.utils.time_utils import current_date, to_time_str


class BaseQmtKdataRecorder(FixedCycleDataRecorder):
    default_size = 50000
    entity_provider: str = "exchange"

    provider = "qmt"

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
    ) -> None:
        level = IntervalLevel(level)
        self.adjust_type = AdjustType(adjust_type)
        self.entity_type = self.entity_schema.__name__.lower()

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

    def record(self, entity, start, end, size, timestamps):
        if not start:
            start = "2005-01-01"
        if not end:
            end = current_date()
        df = qmt_quote.get_kdata(
            entity_id=entity.id,
            start_timestamp=start,
            end_timestamp=end,
            adjust_type=self.adjust_type,
            level=self.level,
        )
        if pd_is_not_null(df):
            df["entity_id"] = entity.id
            df["timestamp"] = pd.to_datetime(df.index)
            df["id"] = df.apply(lambda row: f"{row['entity_id']}_{to_time_str(row['timestamp'])}", axis=1)
            df["provider"] = "qmt"
            df["level"] = self.level.value
            df["code"] = entity.code
            df["name"] = entity.name
            df.rename(columns={"amount": "turnover"}, inplace=True)
            df["change_pct"] = (df["close"] - df["preClose"]) / df["preClose"]
            df_to_db(df=df, data_schema=self.data_schema, provider=self.provider, force_update=self.force_update)
        else:
            self.logger.info(f"no kdata for {entity.id}")


class EMStockKdataRecorder(BaseQmtKdataRecorder):
    entity_schema = Stock
    data_schema = StockKdataCommon


if __name__ == "__main__":
    # Stock.record_data(provider="exchange")
    EMStockKdataRecorder(entity_id="stock_sz_000338", adjust_type=AdjustType.hfq).run()


# the __all__ is generated
__all__ = ["BaseQmtKdataRecorder", "EMStockKdataRecorder"]
