from typing import List, Union

import pandas as pd

from zvt.api.common import get_kdata_schema
from zvt.api.computing import ma, macd
from zvt.domain import SecurityType, TradingLevel, Provider
from zvt.factors.factor import FilterFactor
from zvt.utils.pd_utils import index_df_with_security_time


class TechnicalFactor(FilterFactor):
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
                 provider: Union[str, Provider] = 'netease',
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

        super().__init__(self.data_schema, security_list, security_type, exchanges, codes, the_timestamp,
                         start_timestamp, end_timestamp, columns, filters, provider, level, real_time, refresh_interval,
                         category_field, keep_all_timestamp=False, fill_method=None, effective_number=None)

    def depth_computing(self):
        self.depth_df = self.data_df.reset_index(level='timestamp')

        for idx, indicator in enumerate(self.indicators):
            if indicator == 'ma':
                window = self.indicators_param[idx].get('window')

                for security_id, df in self.depth_df.groupby('security_id'):
                    if self.security_type == SecurityType.stock:
                        self.depth_df.loc[security_id, 'ma{}'.format(window)] = ma(df['qfq_close'], window=window)
                    else:
                        self.depth_df.loc[security_id, 'ma{}'.format(window)] = ma(df['close'], window=window)
            if indicator == 'macd':
                slow = self.indicators_param[idx].get('slow')
                fast = self.indicators_param[idx].get('fast')
                n = self.indicators_param[idx].get('n')

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
                 provider: Union[str, Provider] = 'netease',
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


if __name__ == '__main__':
    # factor = TechnicalFactor(codes=['000338', '300027'], start_timestamp='2019-01-01', end_timestamp='2019-02-01')
    # factor.run()
    # print(factor.get_data_df())
    # factor.move_on()
    # print(factor.get_data_df())

    factor1 = CrossMaFactor(security_list=['coin_binance_EOS/USDT'],
                            security_type=SecurityType.coin,
                            start_timestamp='2019-01-01',
                            end_timestamp='2019-06-05', level=TradingLevel.LEVEL_5MIN, provider='ccxt')
    factor1.compute()
    factor1.draw()
    factor1.draw_depth(value_field='ma10')
    factor1.draw_result(value_field='score')
