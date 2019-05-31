from zvt.api.common import get_kdata_schema
from zvt.api.computing import ma, macd
from zvt.domain import SecurityType, TradingLevel
from zvt.factors.factor import OneSchemaFactor, MustFactor, OneSchemaMustFactor


class TechnicalFactor(OneSchemaFactor):
    def __init__(self, security_type=SecurityType.stock, exchanges=['sh', 'sz'], codes=None, the_timestamp=None,
                 start_timestamp=None, end_timestamp=None, keep_all_timestamp=False, fill_method='ffill', filters=None,
                 provider='netease', level=TradingLevel.LEVEL_1DAY,
                 indicators=['ma', 'macd'],
                 indicators_param=[{'window': 5}, {'slow': 26, 'fast': 12, 'n': 9}]) -> None:
        """
        this base class is for init the kdata,you could calculate technical factor from it

        :param security_type:
        :type security_type:
        :param exchanges:
        :type exchanges:
        :param codes:
        :type codes:
        :param the_timestamp:
        :type the_timestamp:
        :param start_timestamp:
        :type start_timestamp:
        :param end_timestamp:
        :type end_timestamp:
        :param keep_all_timestamp:
        :type keep_all_timestamp:
        :param fill_method:
        :type fill_method:
        :param filters:
        :type filters:
        :param provider:
        :type provider:
        :param level:
        :type level:
        :param indicators: the technical factors need to calculate
        :type indicators:

        """
        self.indicators = indicators
        self.indicators_param = indicators_param
        self.data_schema = get_kdata_schema(security_type, level=level)

        super().__init__(security_type, exchanges, codes, the_timestamp, None, None, start_timestamp,
                         end_timestamp, keep_all_timestamp, fill_method, None, filters, provider, level=level)

    def run(self):
        for idx, factor in enumerate(self.indicators):
            if factor == 'ma':
                window = self.indicators_param[idx].get('window')
                if self.security_type == SecurityType.stock:
                    self.data_df['ma{}'.format(window)] = ma(self.data_df['qfq_close'], window=window)
                else:
                    self.data_df['ma{}'.format(window)] = ma(self.data_df['close'], window=window)
            if factor == 'macd':
                slow = self.indicators_param[idx].get('slow')
                fast = self.indicators_param[idx].get('fast')
                n = self.indicators_param[idx].get('n')

                if self.security_type == SecurityType.stock:
                    diff, dea, m = macd(self.data_df['qfq_close'], slow=slow, fast=fast, n=n)
                else:
                    diff, dea, m = macd(self.data_df['close'], slow=slow, fast=fast, n=n)

                self.data_df['diff'] = diff
                self.data_df['dea'] = dea
                self.data_df['m'] = m


class CrossMaFactor(TechnicalFactor, MustFactor):
    def __init__(self, security_type=SecurityType.stock, exchanges=['sh', 'sz'], codes=None, the_timestamp=None,
                 start_timestamp=None, end_timestamp=None, keep_all_timestamp=False, fill_method='ffill', filters=None,
                 provider='netease', level=TradingLevel.LEVEL_1DAY, short_window=5, long_window=10) -> None:
        super().__init__(security_type, exchanges, codes, the_timestamp, start_timestamp, end_timestamp,
                         keep_all_timestamp, fill_method, filters, provider, level, indicators=['ma', 'ma'],
                         indicators_param=[{'window': short_window}, {'window': long_window}])

        self.short_window = short_window
        self.long_window = long_window

    def run(self):
        super().run()
        s = self.data_df['ma{}'.format(self.short_window)] > self.data_df['ma{}'.format(self.long_window)]
        self.df = s.to_frame(name='score')


class IndexFactor(OneSchemaMustFactor):
    def __init__(self, security_type=SecurityType.index, exchanges=['cn'], codes=None, the_timestamp=None,
                 window=None, window_func='mean', start_timestamp=None, end_timestamp=None, keep_all_timestamp=False,
                 fill_method='ffill', columns=[], filters=None, provider='sina', level=TradingLevel.LEVEL_1DAY,
                 effective_number=10) -> None:
        super().__init__(security_type, exchanges, codes, the_timestamp, window, window_func, start_timestamp,
                         end_timestamp, keep_all_timestamp, fill_method, columns, filters, provider, level,
                         effective_number)

    def run(self):
        pass


if __name__ == '__main__':
    factor = CrossMaFactor(codes=['000338'], start_timestamp='2019-01-01', end_timestamp='2019-05-29')
    factor.run()
    print(factor.get_df())
