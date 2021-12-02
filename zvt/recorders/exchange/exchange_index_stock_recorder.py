# -*- coding: utf-8 -*-

from typing import List

import pandas as pd
import requests

from zvt.contract.api import df_to_db
from zvt.contract.recorder import TimestampsDataRecorder
from zvt.domain import Index, IndexStock
from zvt.recorders.exchange.api import cs_index_stock_api, cn_index_stock_api
from zvt.utils.time_utils import pre_month_start_date
from zvt.utils.time_utils import to_pd_timestamp


class ExchangeIndexStockRecorder(TimestampsDataRecorder):
    entity_provider = "exchange"
    entity_schema = Index

    provider = "exchange"
    data_schema = IndexStock

    def __init__(
        self,
        force_update=False,
        sleeping_time=5,
        exchanges=None,
        entity_ids=None,
        code=None,
        codes=None,
        day_data=False,
        entity_filters=None,
        ignore_failed=True,
        real_time=False,
        fix_duplicate_way="add",
        start_timestamp=None,
        end_timestamp=None,
        record_history=False,
    ) -> None:
        super().__init__(
            force_update,
            sleeping_time,
            exchanges,
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
        )
        self.record_history = record_history

    def init_timestamps(self, entity_item) -> List[pd.Timestamp]:
        last_valid_date = pre_month_start_date()
        if self.record_history:
            # 每个月记录一次
            return [to_pd_timestamp(item) for item in pd.date_range(entity_item.list_date, last_valid_date, freq="M")]
        else:
            return [last_valid_date]

    def record(self, entity, start, end, size, timestamps):
        if entity.publisher == "cnindex":
            for timestamp in timestamps:
                df = cn_index_stock_api.get_cn_index_stock(code=entity.code, timestamp=timestamp, name=entity.name)
                df_to_db(data_schema=self.data_schema, df=df, provider=self.provider, force_update=True)
        elif entity.publisher == "csindex":
            # cs index not support history data
            df = cs_index_stock_api.get_cs_index_stock(code=entity.code, timestamp=None, name=entity.name)
            df_to_db(data_schema=self.data_schema, df=df, provider=self.provider, force_update=True)


if __name__ == "__main__":
    # ExchangeIndexMetaRecorder().run()
    ExchangeIndexStockRecorder(codes=["399370"]).run()
# the __all__ is generated
__all__ = ["ExchangeIndexStockRecorder"]
