from typing import List, Union

import pandas as pd
import plotly.graph_objs as go

from zvt.api.common import get_kdata_schema
from zvt.api.computing import ma, macd
from zvt.charts import Chart
from zvt.domain import SecurityType, TradingLevel, Provider
from zvt.factors.factor import FilterFactor
from zvt.utils.pd_utils import index_df_with_security_time


class TechnicalFactor(FilterFactor):

    def __json__(self):
        return {
            'indicators': self.indicators,
            'indicators_param': self.indicators_param,
            'indicator_cols': list(self.indicator_cols)
        }

    for_json = __json__  # supported by simplejson

    def __init__(self,
                 security_list: List[str] = None,
                 security_type: Union[str, SecurityType] = SecurityType.stock,
                 exchanges: List[str] = ['sh', 'sz'],
                 codes: List[str] = None,
                 the_timestamp: Union[str, pd.Timestamp] = None,
                 start_timestamp: Union[str, pd.Timestamp] = None,
                 end_timestamp: Union[str, pd.Timestamp] = None,
                 columns: List = None,
                 filters: List = None,
                 provider: Union[str, Provider] = 'joinquant',
                 level: TradingLevel = TradingLevel.LEVEL_1DAY,
                 real_time: bool = False,
                 refresh_interval: int = 10,
                 category_field: str = 'security_id',
                 # child added arguments
                 indicators=['ma', 'macd'],
                 indicators_param=[{'window': 5}, {'slow': 26, 'fast': 12, 'n': 9}],
                 valid_window=26
                 ) -> None:
        self.indicators = indicators
        self.indicators_param = indicators_param
        self.data_schema = get_kdata_schema(security_type, level=level)
        self.valid_window = valid_window
        self.indicator_cols = set()

        super().__init__(self.data_schema, security_list, security_type, exchanges, codes, the_timestamp,
                         start_timestamp, end_timestamp, columns, filters, provider, level, real_time, refresh_interval,
                         category_field, keep_all_timestamp=False, fill_method=None, effective_number=None)

    def depth_computing(self):
        self.depth_df = self.data_df.reset_index(level='timestamp')

        for idx, indicator in enumerate(self.indicators):
            if indicator == 'ma':
                window = self.indicators_param[idx].get('window')

                col = 'ma{}'.format(window)
                self.indicator_cols.add(col)

                for security_id, df in self.depth_df.groupby('security_id'):
                    if self.security_type == SecurityType.stock:
                        self.depth_df.loc[security_id, col] = ma(df['qfq_close'], window=window)
                    else:
                        self.depth_df.loc[security_id, col] = ma(df['close'], window=window)
            if indicator == 'macd':
                slow = self.indicators_param[idx].get('slow')
                fast = self.indicators_param[idx].get('fast')
                n = self.indicators_param[idx].get('n')

                self.indicator_cols.add('diff')
                self.indicator_cols.add('dea')
                self.indicator_cols.add('macd')

                for security_id, df in self.depth_df.groupby('security_id'):
                    if self.security_type == SecurityType.stock:
                        diff, dea, m = macd(df['qfq_close'], slow=slow, fast=fast, n=n)
                    else:
                        diff, dea, m = macd(df['close'], slow=slow, fast=fast, n=n)

                    self.depth_df.loc[security_id, 'diff'] = diff
                    self.depth_df.loc[security_id, 'dea'] = dea
                    self.depth_df.loc[security_id, 'macd'] = m

        self.depth_df = self.depth_df.set_index('timestamp', append=True)

    def on_category_data_added(self, category, added_data: pd.DataFrame):
        size = len(added_data)
        df = self.data_df.loc[category].iloc[-self.valid_window - size:]

        for idx, indicator in enumerate(self.indicators):
            if indicator == 'ma':
                window = self.indicators_param[idx].get('window')

                if self.security_type == SecurityType.stock:
                    df['ma{}'.format(window)] = ma(df['qfq_close'], window=window)
                else:
                    df['ma{}'.format(window)] = ma(df['close'], window=window)

            if indicator == 'macd':
                slow = self.indicators_param[idx].get('slow')
                fast = self.indicators_param[idx].get('fast')
                n = self.indicators_param[idx].get('n')

                if self.security_type == SecurityType.stock:
                    df['diff'], df['dea'], df['m'] = macd(df['qfq_close'], slow=slow, fast=fast, n=n)
                else:
                    df['diff'], df['dea'], df['m'] = macd(df['close'], slow=slow, fast=fast, n=n)

        df = df.iloc[-size:, ]
        df = df.reset_index()
        df[self.category_field] = category
        df = index_df_with_security_time(df)

        self.depth_df = self.depth_df.append(df)
        self.depth_df = self.depth_df.sort_index(level=[0, 1])

    def draw_with_indicators(self, render='html', file_name=None, width=None,
                             height=None, title=None, keep_ui_state=True, annotation_df=None,
                             indicators=['ma5', 'ma10']):
        indicator_cols = self.indicator_cols
        if indicators:
            indicator_cols = self.indicator_cols & set(indicators)

        figures = [go.Candlestick]
        value_fields = [None]
        modes = [None]
        for indicator_col in indicator_cols:
            figures.append(go.Scatter)
            value_fields.append(indicator_col)
            modes.append('lines')

        chart = Chart(category_field=self.category_field, figures=figures, modes=modes,
                      value_fields=value_fields,
                      render=render, file_name=file_name,
                      width=width, height=height, title=title, keep_ui_state=keep_ui_state)
        chart.set_data_df(self.depth_df)
        chart.set_annotation_df(annotation_df)
        return chart.draw()


class CrossMaFactor(TechnicalFactor):
    def __init__(self,
                 security_list: List[str] = None,
                 security_type: Union[str, SecurityType] = SecurityType.stock,
                 exchanges: List[str] = ['sh', 'sz'],
                 codes: List[str] = None,
                 the_timestamp: Union[str, pd.Timestamp] = None,
                 start_timestamp: Union[str, pd.Timestamp] = None,
                 end_timestamp: Union[str, pd.Timestamp] = None,
                 columns: List = None, filters: List = None,
                 provider: Union[str, Provider] = 'joinquant',
                 level: TradingLevel = TradingLevel.LEVEL_1DAY,
                 real_time: bool = False,
                 refresh_interval: int = 10,
                 category_field: str = 'security_id',
                 # child added arguments
                 short_window=5,
                 long_window=10) -> None:
        self.short_window = short_window
        self.long_window = long_window

        super().__init__(security_list, security_type, exchanges, codes, the_timestamp, start_timestamp, end_timestamp,
                         columns, filters, provider, level, real_time, refresh_interval, category_field,
                         indicators=['ma', 'ma'],
                         indicators_param=[{'window': short_window}, {'window': long_window}], valid_window=long_window)

    def compute(self):
        super().compute()
        s = self.depth_df['ma{}'.format(self.short_window)] > self.depth_df['ma{}'.format(self.long_window)]
        self.result_df = s.to_frame(name='score')

    def on_category_data_added(self, category, added_data: pd.DataFrame):
        super().on_category_data_added(category, added_data)
        # TODO:improve it to just computing the added data
        self.compute()


class BullFactor(TechnicalFactor):
    def __init__(self, security_list: List[str] = None, security_type: Union[str, SecurityType] = SecurityType.stock,
                 exchanges: List[str] = ['sh', 'sz'], codes: List[str] = None,
                 the_timestamp: Union[str, pd.Timestamp] = None, start_timestamp: Union[str, pd.Timestamp] = None,
                 end_timestamp: Union[str, pd.Timestamp] = None, columns: List = None, filters: List = None,
                 provider: Union[str, Provider] = 'joinquant', level: TradingLevel = TradingLevel.LEVEL_1DAY,
                 real_time: bool = False, refresh_interval: int = 10, category_field: str = 'security_id',
                 indicators=['macd'], indicators_param=[{'slow': 26, 'fast': 12, 'n': 9}],
                 valid_window=26) -> None:
        super().__init__(security_list, security_type, exchanges, codes, the_timestamp, start_timestamp, end_timestamp,
                         columns, filters, provider, level, real_time, refresh_interval, category_field, indicators,
                         indicators_param, valid_window)

    def compute(self):
        super().compute()
        s = (self.depth_df['diff'] > 0) & (self.depth_df['dea'] > 0)
        self.result_df = s.to_frame(name='score')


if __name__ == '__main__':
    factor = BullFactor(codes=['000338'], start_timestamp='2018-01-01', end_timestamp='2019-02-01')
    factor.draw_result()
