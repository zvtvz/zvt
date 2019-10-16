from typing import List, Union

import pandas as pd

from zvdata import IntervalLevel
from zvt.api.common import get_kdata_schema
from zvt.factors.algorithm import MacdTransformer
from zvt.factors.factor import Factor, Transformer, Accumulator


class TechnicalFactor(Factor):
    def __init__(self,
                 entity_ids: List[str] = None,
                 entity_type: str = 'stock',
                 exchanges: List[str] = ['sh', 'sz'],
                 codes: List[str] = None,
                 the_timestamp: Union[str, pd.Timestamp] = None,
                 start_timestamp: Union[str, pd.Timestamp] = None,
                 end_timestamp: Union[str, pd.Timestamp] = None,
                 columns: List = None,
                 filters: List = None,
                 order: object = None,
                 limit: int = None,
                 provider: str = 'joinquant',
                 level: Union[str, IntervalLevel] = IntervalLevel.LEVEL_1DAY,
                 category_field: str = 'entity_id',
                 time_field: str = 'timestamp',
                 computing_window: int = 250,
                 keep_all_timestamp: bool = False,
                 fill_method: str = 'ffill',
                 effective_number: int = 10,
                 transformers: List[Transformer] = [MacdTransformer()],
                 accumulator: Accumulator = None,
                 need_persist: bool = False,
                 dry_run: bool = True) -> None:
        self.data_schema = get_kdata_schema(entity_type, level=level)

        self.indicator_cols = []
        for transformer in transformers:
            self.indicator_cols += transformer.indicator_cols

        if not columns:
            if entity_type == 'stock':
                columns = ['id', 'entity_id', 'timestamp', 'qfq_open', 'qfq_close', 'qfq_high', 'qfq_low']
            else:
                columns = ['id', 'entity_id', 'timestamp', 'open', 'close', 'high', 'low']

        super().__init__(self.data_schema, entity_ids, entity_type, exchanges, codes, the_timestamp, start_timestamp,
                         end_timestamp, columns, filters, order, limit, provider, level, category_field, time_field,
                         computing_window, keep_all_timestamp, fill_method, effective_number,
                         transformers, accumulator, need_persist, dry_run)

    def pre_compute(self):
        self.data_df.rename(columns={'qfq_open': 'open', 'qfq_close': 'close', 'qfq_high': 'high', 'qfq_low': 'low', },
                            inplace=True)
        super().pre_compute()

    def __json__(self):
        result = super().__json__()
        result['indicator_cols'] = self.indicator_cols
        return result

    for_json = __json__  # supported by simplejson
