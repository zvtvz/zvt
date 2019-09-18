from typing import List, Union

import pandas as pd

from zvdata import IntervalLevel
from zvdata.factor import Factor
from zvdata.utils.pd_utils import df_is_not_null
from zvdata.utils.pd_utils import index_df_with_category_xfield
from zvt.api.common import get_kdata_schema
from zvt.api.computing import ma, macd


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
                 level: IntervalLevel = IntervalLevel.LEVEL_1DAY,
                 category_field: str = 'entity_id',
                 time_field: str = 'timestamp',
                 trip_timestamp: bool = True,
                 auto_load: bool = True,
                 # child added arguments
                 fq='qfq',
                 indicators=['ma', 'macd'],
                 indicators_param=[{'window': 5}, {'slow': 26, 'fast': 12, 'n': 9}],
                 valid_window=26
                 ) -> None:
        self.fq = fq
        self.indicators = indicators
        self.indicators_param = indicators_param
        self.data_schema = get_kdata_schema(entity_type, level=level)
        self.valid_window = valid_window
        self.indicator_cols = set()

        super().__init__(self.data_schema, entity_ids, entity_type, exchanges, codes, the_timestamp, start_timestamp,
                         end_timestamp, columns, filters, order, limit, provider, level, category_field, time_field,
                         trip_timestamp, auto_load, keep_all_timestamp=False,
                         fill_method=None, effective_number=None)

    def do_compute(self):
        if df_is_not_null(self.data_df):
            for idx, indicator in enumerate(self.indicators):
                if indicator == 'ma':
                    window = self.indicators_param[idx].get('window')

                    col = 'ma{}'.format(window)
                    self.indicator_cols.add(col)

                    if self.entity_type == 'stock' and self.fq == 'qfq':
                        df = self.depth_df['qfq_close'].groupby(level=0).rolling(window=window,
                                                                                 min_periods=window).mean()
                    else:
                        df = self.depth_df['close'].groupby(level=0).rolling(window=window, min_periods=window).mean()

                    df = df.reset_index(level=0, drop=True)

                    self.depth_df[col] = df
                    # self.depth_df = pd.concat([self.depth_df, df], axis=1, sort=False)

                if indicator == 'macd':
                    slow = self.indicators_param[idx].get('slow')
                    fast = self.indicators_param[idx].get('fast')
                    n = self.indicators_param[idx].get('n')

                    self.indicator_cols.add('diff')
                    self.indicator_cols.add('dea')
                    self.indicator_cols.add('macd')

                    # for entity_id, df in self.depth_df.groupby('entity_id'):
                    #     if self.entity_type == 'stock' and self.fq == 'qfq':
                    #         diff, dea, m = macd(df['qfq_close'], slow=slow, fast=fast, n=n)
                    #     else:
                    #         diff, dea, m = macd(df['close'], slow=slow, fast=fast, n=n)
                    #
                    #     self.depth_df.loc[entity_id, 'diff'] = diff
                    #     self.depth_df.loc[entity_id, 'dea'] = dea
                    #     self.depth_df.loc[entity_id, 'macd'] = m

                    if self.entity_type == 'stock' and self.fq == 'qfq':
                        df = self.depth_df.groupby(level=0)['qfq_close'].apply(
                            lambda x: macd(x, slow=slow, fast=fast, n=n, return_type='df'))
                    else:
                        df = self.depth_df.groupby(level=0)['close'].apply(
                            lambda x: macd(x, slow=slow, fast=fast, n=n, return_type='df'))
                    self.depth_df = pd.concat([self.depth_df, df], axis=1, sort=False)

            # self.depth_df = self.depth_df.set_index('timestamp', append=True)

    def on_category_data_added(self, category, added_data: pd.DataFrame):
        size = len(added_data)
        df = self.data_df.loc[category].iloc[-self.valid_window - size:]

        for idx, indicator in enumerate(self.indicators):
            if indicator == 'ma':
                window = self.indicators_param[idx].get('window')

                if self.entity_type == 'stock':
                    df['ma{}'.format(window)] = ma(df['qfq_close'], window=window)
                else:
                    df['ma{}'.format(window)] = ma(df['close'], window=window)

            if indicator == 'macd':
                slow = self.indicators_param[idx].get('slow')
                fast = self.indicators_param[idx].get('fast')
                n = self.indicators_param[idx].get('n')

                if self.entity_type == 'stock':
                    df['diff'], df['dea'], df['m'] = macd(df['qfq_close'], slow=slow, fast=fast, n=n)
                else:
                    df['diff'], df['dea'], df['m'] = macd(df['close'], slow=slow, fast=fast, n=n)

        df = df.iloc[-size:, ]
        df = df.reset_index()
        df[self.category_field] = category
        df = index_df_with_category_xfield(df)

        self.depth_df = self.depth_df.append(df)
        self.depth_df = self.depth_df.sort_index(level=[0, 1])

    def draw_depth(self, chart='kline', plotly_layout=None, annotation_df=None, render='html', file_name=None,
                   width=None, height=None, title=None, keep_ui_state=True, **kwargs):
        return super().draw_depth('kline', plotly_layout, render, file_name, width, height, title, keep_ui_state,
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
        s = self.depth_df['ma{}'.format(self.short_window)] > self.depth_df['ma{}'.format(self.long_window)]
        self.result_df = s.to_frame(name='score')

    def on_category_data_added(self, category, added_data: pd.DataFrame):
        super().on_category_data_added(category, added_data)
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
        s = (self.depth_df['diff'] > 0) & (self.depth_df['dea'] > 0)
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
