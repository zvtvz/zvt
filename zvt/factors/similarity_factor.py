# -*- coding: utf-8 -*-
from typing import List, Union

import numpy as np
import pandas as pd

from zvt.api import AdjustType, get_kdata, get_kdata_schema
from zvt.contract import EntityMixin, IntervalLevel
from zvt.domain import Stock
from zvt.factors import TechnicalFactor, Transformer, Accumulator


def get_ref_vector(entity_id, end, window=100, level=IntervalLevel.LEVEL_1DAY, entity_schema=Stock):
    data_schema = get_kdata_schema(entity_schema.__name__, level=level)

    df = get_kdata(entity_id=entity_id, level=level, end_timestamp=end, order=data_schema.timestamp.desc(),
                   limit=window,
                   columns=['close', 'volume'])

    exp_data = np.zeros((window, 2))
    exp_data[:, 0] = df['close']
    exp_data[:, 1] = df['volume']

    return exp_data


class SimilarityFactor(TechnicalFactor):

    def __init__(self, entity_schema: EntityMixin = Stock, provider: str = None, entity_provider: str = None,
                 entity_ids: List[str] = None, exchanges: List[str] = None, codes: List[str] = None,
                 the_timestamp: Union[str, pd.Timestamp] = None, start_timestamp: Union[str, pd.Timestamp] = None,
                 end_timestamp: Union[str, pd.Timestamp] = None,
                 columns: List = ['id', 'entity_id', 'timestamp', 'level', 'open', 'close', 'high', 'low'],
                 filters: List = None, order: object = None, limit: int = None,
                 level: Union[str, IntervalLevel] = IntervalLevel.LEVEL_1DAY, category_field: str = 'entity_id',
                 time_field: str = 'timestamp', computing_window: int = None, keep_all_timestamp: bool = False,
                 fill_method: str = 'ffill', effective_number: int = None, transformer: Transformer = None,
                 accumulator: Accumulator = None, need_persist: bool = False, dry_run: bool = False,
                 adjust_type: Union[AdjustType, str] = None, entity_id='stock_sz_000338', end='2020-01-01',
                 window=100) -> None:
        self.ref_vector = get_ref_vector(entity_id=entity_id, end=end, window=window)
        super().__init__(entity_schema, provider, entity_provider, entity_ids, exchanges, codes, the_timestamp,
                         start_timestamp, end_timestamp, columns, filters, order, limit, level, category_field,
                         time_field, computing_window, keep_all_timestamp, fill_method, effective_number, transformer,
                         accumulator, need_persist, dry_run, adjust_type)
