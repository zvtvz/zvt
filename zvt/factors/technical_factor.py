import time

from zvt.api.common import get_kdata_schema
from zvt.api.computing import ma, macd
from zvt.domain import SecurityType, TradingLevel
from zvt.factors.factor import OneSchemaFactor, MustFactor, OneSchemaScoreFactor
from zvt.utils.pd_utils import index_df_with_security_time


class TechnicalFactor(OneSchemaFactor):

    def __init__(self, security_list=None, security_type=SecurityType.stock, exchanges=['sh', 'sz'], codes=None,
                 the_timestamp=None, start_timestamp=None, end_timestamp=None, columns=[], filters=None,
                 provider='netease', level=TradingLevel.LEVEL_1DAY, indicators=['ma', 'macd'],
                 indicators_param=[{'window': 5}, {'slow': 26, 'fast': 12, 'n': 9}], valid_window=26) -> None:
        self.indicators = indicators
        self.indicators_param = indicators_param
        self.data_schema = get_kdata_schema(security_type, level=level)
        self.valid_window = valid_window

        super().__init__(self.data_schema, security_list, security_type, exchanges, codes, the_timestamp,
                         start_timestamp, end_timestamp,
                         False, None, columns, filters, provider, level, None)

    def depth_computing(self):
        self.data_df = self.original_df.reset_index(level='timestamp')

        for idx, indicator in enumerate(self.indicators):
            if indicator == 'ma':
                window = self.indicators_param[idx].get('window')

                for security_id, df in self.data_df.groupby('security_id'):
                    if self.security_type == SecurityType.stock:
                        self.data_df.loc[security_id, 'ma{}'.format(window)] = ma(df['qfq_close'], window=window)
                    else:
                        self.data_df.loc[security_id, 'ma{}'.format(window)] = ma(df['close'], window=window)
            if indicator == 'macd':
                slow = self.indicators_param[idx].get('slow')
                fast = self.indicators_param[idx].get('fast')
                n = self.indicators_param[idx].get('n')

                for security_id, df in self.data_df.groupby('security_id'):
                    if self.security_type == SecurityType.stock:
                        diff, dea, m = macd(df['qfq_close'], slow=slow, fast=fast, n=n)
                    else:
                        diff, dea, m = macd(df['close'], slow=slow, fast=fast, n=n)

                    self.data_df.loc[security_id, 'diff'] = diff
                    self.data_df.loc[security_id, 'dea'] = dea
                    self.data_df.loc[security_id, 'm'] = m

        self.data_df = self.data_df.set_index('timestamp', append=True)

    def on_data_added(self, security_id, size):
        df = self.original_df.loc[security_id].iloc[-self.valid_window - size:]

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
        df['security_id'] = security_id
        df = index_df_with_security_time(df)

        self.data_df = self.data_df.append(df)
        self.data_df = self.data_df.sort_index(level=[0, 1])


class CrossMaFactor(TechnicalFactor, MustFactor):

    def __init__(self, security_list=None, security_type=SecurityType.stock, exchanges=['sh', 'sz'], codes=None,
                 the_timestamp=None, start_timestamp=None, end_timestamp=None, columns=[], filters=None,
                 provider='netease',
                 level=TradingLevel.LEVEL_1DAY, short_window=5, long_window=10) -> None:
        super().__init__(security_list, security_type, exchanges, codes, the_timestamp, start_timestamp, end_timestamp,
                         columns, filters, provider, level, indicators=['ma', 'ma'],
                         indicators_param=[{'window': short_window}, {'window': long_window}])

        self.short_window = short_window
        self.long_window = long_window

    def run(self):
        super().run()
        s = self.data_df['ma{}'.format(self.short_window)] > self.data_df['ma{}'.format(self.long_window)]
        self.df = s.to_frame(name='score')

    def on_data_added(self, security_id, size):
        super().on_data_added(security_id, size)
        s = self.data_df['ma{}'.format(self.short_window)] > self.data_df['ma{}'.format(self.long_window)]
        self.df = s.to_frame(name='score')


class IndexMoneyFlowFactor(OneSchemaScoreFactor):
    def __init__(self, security_list=None, security_type=SecurityType.index, exchanges=['cn'], codes=None,
                 the_timestamp=None,
                 window=None, window_func='mean', start_timestamp=None, end_timestamp=None, keep_all_timestamp=False,
                 fill_method='ffill', columns=[], filters=None, provider='sina', level=TradingLevel.LEVEL_1DAY,
                 effective_number=10) -> None:
        super().__init__(security_list, security_type, exchanges, codes, the_timestamp, window, window_func,
                         start_timestamp, end_timestamp, keep_all_timestamp, fill_method, columns, filters, provider,
                         level, effective_number)

    def run(self):
        pass


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
    factor1.run()
    print(factor1.get_df())
    while True:
        factor1.move_on()
        print(factor1.get_df())
        time.sleep(10)
