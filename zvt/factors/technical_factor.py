from zvt.api.common import get_kdata_schema
from zvt.domain import SecurityType, TradingLevel
from zvt.factors.factor import OneSchemaMustFactor


class CrossMaFactor(OneSchemaMustFactor):
    def __init__(self, security_type=SecurityType.stock, exchanges=['sh', 'sz'], codes=None, the_timestamp=None,
                 window=None, window_func='mean', start_timestamp=None, end_timestamp=None, keep_all_timestamp=False,
                 fill_method='ffill', columns=['qfq_close'], filters=None, provider='netease',
                 level=TradingLevel.LEVEL_1DAY,
                 short_window=5, long_window=10) -> None:
        self.data_schema = get_kdata_schema(security_type, level=level)
        columns = [self.data_schema.qfq_close]
        self.short_window = short_window
        self.long_window = long_window

        super().__init__(security_type, exchanges, codes, the_timestamp, window, window_func, start_timestamp,
                         end_timestamp, keep_all_timestamp, fill_method, columns, filters, provider, level=level)

    def run(self):
        short_df = self.calculate_ma(self.short_window)
        long_df = self.calculate_ma(self.long_window)
        self.df = short_df.loc[long_df.index, :] > long_df

        self.fill_gap()

    def calculate_ma(self, window):
        df = self.original_df.reset_index(level='timestamp')

        df = df.groupby(level=0).rolling(window='{}D'.format(window), on='timestamp').mean()
        df = df.reset_index(level=0, drop=True)
        df = df.set_index('timestamp', append=True)

        df = df.loc[(slice(None), slice(self.start_timestamp, self.end_timestamp)), :]
        return df


if __name__ == '__main__':
    factor = CrossMaFactor(codes=['000338'], start_timestamp='2018-01-01', end_timestamp='2019-05-01')
    factor.run()

    print(factor.get_df())
