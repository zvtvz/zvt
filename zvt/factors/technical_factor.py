from typing import List, Union

import pandas as pd

from zvdata import IntervalLevel
from zvt.api.common import get_kdata_schema
from zvt.factors.algorithm import MacdTransformer, MaTransformer
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
                 computing_window: int = None,
                 keep_all_timestamp: bool = False,
                 fill_method: str = 'ffill',
                 effective_number: int = 10,
                 transformer: Transformer = MacdTransformer(),
                 accumulator: Accumulator = None,
                 persist_factor: bool = False,
                 dry_run: bool = True) -> None:
        self.data_schema = get_kdata_schema(entity_type, level=level)

        if transformer:
            self.indicator_cols = transformer.indicator_cols

        if not columns:
            columns = ['id', 'entity_id', 'timestamp', 'level', 'open', 'close', 'high', 'low']

        super().__init__(self.data_schema, entity_ids, entity_type, exchanges, codes, the_timestamp, start_timestamp,
                         end_timestamp, columns, filters, order, limit, provider, level, category_field, time_field,
                         computing_window, keep_all_timestamp, fill_method, effective_number,
                         transformer, accumulator, persist_factor, dry_run)

    def __json__(self):
        result = super().__json__()
        result['indicator_cols'] = self.indicator_cols
        return result

    for_json = __json__  # supported by simplejson

class BullFactor(TechnicalFactor):
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
                 persist_factor: bool = False, dry_run: bool = False) -> None:
        transformer = MacdTransformer()

        super().__init__(entity_ids, entity_type, exchanges, codes, the_timestamp, start_timestamp, end_timestamp,
                         columns, filters, order, limit, provider, level, category_field, time_field, 26,
                         False, None, None, transformer, None, persist_factor, dry_run)

    def do_compute(self):
        super().do_compute()
        s = (self.factor_df['diff'] > 0) & (self.factor_df['dea'] > 0)
        self.result_df = s.to_frame(name='score')


if __name__ == '__main__':
    factor = TechnicalFactor(entity_type='stock',
                             codes=['000338'],
                             start_timestamp='2019-01-01',
                             end_timestamp='2019-06-10',
                             level=IntervalLevel.LEVEL_1DAY,
                             provider='joinquant',
                             computing_window=26,
                             transformer=MacdTransformer())

    print(factor.get_factor_df().tail())

    factor.move_on(to_timestamp='2019-06-17')
    diff = factor.get_factor_df()['diff']
    dea = factor.get_factor_df()['dea']
    macd = factor.get_factor_df()['macd']

    assert round(diff.loc[('stock_sz_000338', '2019-06-17')], 2) == 0.06
    assert round(dea.loc[('stock_sz_000338', '2019-06-17')], 2) == -0.03
    assert round(macd.loc[('stock_sz_000338', '2019-06-17')], 2) == 0.19
