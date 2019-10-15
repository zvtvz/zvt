from typing import List, Union

import pandas as pd

from zvdata import IntervalLevel
from zvdata.factor import Factor
from zvdata.scorer import Transformer, Accumulator
from zvt.api.common import get_kdata_schema
from zvt.api.computing import macd


class MaTransformer(Transformer):
    def __init__(self, windows=[5, 10]) -> None:
        self.windows = windows

    def transform(self, input_df) -> pd.DataFrame:
        for window in self.windows:
            col = 'ma{}'.format(window)
            self.indicator_cols.append(col)

            ma_df = input_df['close'].groupby(level=0).rolling(window=window, min_periods=window).mean()
            ma_df = ma_df.reset_index(level=0, drop=True)
            input_df[col] = ma_df

        return input_df


class MacdTransformer(Transformer):
    def __init__(self, slow=26, fast=12, n=9) -> None:
        self.slow = slow
        self.fast = fast
        self.n = n

        self.indicator_cols.append('diff')
        self.indicator_cols.append('dea')
        self.indicator_cols.append('macd')

    def transform(self, input_df) -> pd.DataFrame:
        macd_df = input_df.groupby(level=0)['close'].apply(
            lambda x: macd(x, slow=self.slow, fast=self.fast, n=self.n, return_type='df'))

        input_df = pd.concat([input_df, macd_df], axis=1, sort=False)
        return input_df


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
                 auto_load: bool = True,
                 valid_window: int = 250,
                 keep_all_timestamp: bool = False,
                 fill_method: str = 'ffill',
                 effective_number: int = 10,
                 transformers: List[Transformer] = [MacdTransformer()],
                 accumulator: Accumulator = None,
                 need_persist: bool = True,
                 dry_run: bool = True) -> None:
        self.data_schema = get_kdata_schema(entity_type, level=level)
        self.indicator_cols = set()
        super().__init__(self.data_schema, entity_ids, entity_type, exchanges, codes, the_timestamp, start_timestamp,
                         end_timestamp, columns, filters, order, limit, provider, level, category_field, time_field,
                         auto_load, valid_window, keep_all_timestamp, fill_method, effective_number,
                         transformers, accumulator, need_persist, dry_run)

    def draw_pipe(self, chart='kline', plotly_layout=None, annotation_df=None, render='html', file_name=None,
                  width=None, height=None, title=None, keep_ui_state=True, **kwargs):
        return super().draw_pipe('kline', plotly_layout, render, file_name, width, height, title, keep_ui_state,
                                 indicators=self.indicator_cols, **kwargs)

    def __json__(self):
        result = super().__json__()
        result['indicator_cols'] = list(self.indicator_cols)
        result['indicators'] = self.indicators
        result['indicators_param'] = self.indicators_param
        return result

    for_json = __json__  # supported by simplejson


class CrossMaFactor(TechnicalFactor):
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
                 level: IntervalLevel = IntervalLevel.LEVEL_1DAY,

                 category_field: str = 'entity_id',
                 auto_load: bool = True,
                 # child added arguments
                 short_window=5,
                 long_window=10) -> None:
        self.short_window = short_window
        self.long_window = long_window

        super().__init__(entity_ids, entity_type, exchanges, codes, the_timestamp, start_timestamp, end_timestamp,
                         columns, filters, order, limit, provider, level, category_field,
                         time_field='timestamp', auto_load=auto_load, fq='qfq', indicators=['ma', 'ma'],
                         indicators_param=[{'window': short_window}, {'window': long_window}], valid_window=long_window)

    def do_compute(self):
        super().do_compute()
        s = self.pipe_df['ma{}'.format(self.short_window)] > self.pipe_df['ma{}'.format(self.long_window)]
        self.result_df = s.to_frame(name='score')

    def on_entity_data_changed(self, entity, added_data: pd.DataFrame):
        super().on_entity_data_changed(entity, added_data)
        # TODO:improve it to just computing the added data
        self.do_compute()


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
                 level: IntervalLevel = IntervalLevel.LEVEL_1DAY,
                 category_field: str = 'entity_id',
                 auto_load: bool = True,
                 indicators=['macd'],
                 indicators_param=[{'slow': 26, 'fast': 12, 'n': 9}],
                 valid_window=26) -> None:
        super().__init__(entity_ids, entity_type, exchanges, codes, the_timestamp, start_timestamp, end_timestamp,
                         columns, filters, order, limit, provider, level, category_field,
                         time_field='timestamp', auto_load=auto_load, fq='qfq', indicators=indicators,
                         indicators_param=indicators_param, valid_window=valid_window)

    def do_compute(self):
        super().do_compute()
        s = (self.pipe_df['diff'] > 0) & (self.pipe_df['dea'] > 0)
        self.result_df = s.to_frame(name='score')


if __name__ == '__main__':
    factor = TechnicalFactor(entity_type='stock',
                             codes=['000338', '000778'],
                             start_timestamp='2019-01-01',
                             end_timestamp='2019-06-10',
                             level=IntervalLevel.LEVEL_1DAY,
                             provider='joinquant',
                             indicators=['macd'],
                             indicators_param=[{'slow': 26, 'fast': 12, 'n': 9}],
                             auto_load=True)
    print(factor.depth_df)
