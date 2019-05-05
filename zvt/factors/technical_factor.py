from zvt.api.common import get_kdata_schema
from zvt.domain import SecurityType, StockDayKdata
from zvt.factors.factor import OneSchemaMustFactor


class CrossMaFactor(OneSchemaMustFactor):
    def __init__(self, security_type=SecurityType.stock, exchanges=['sh', 'sz'], codes=None, the_timestamp=None,
                 window=None, window_func='mean', start_timestamp=None, end_timestamp=None, columns=[StockDayKdata.close],
                 filters=None,
                 provider='eastmoney') -> None:
        self.data_schema = get_kdata_schema(security_type)

        super().__init__(security_type, exchanges, codes, the_timestamp, window, window_func, start_timestamp,
                         end_timestamp, columns, filters, provider)

    def run(self):
        print(self.original_df > self.data_df)
        # ma_df = computing.ma(security_id=self.security_id, start_timestamp=self.start_timestamp,
        #                      end_timestamp=self.end_timestamp,
        #                      provider=Provider.SINA,
        #                      window=self.window)
        # ma_df['value'] = ma_df['close'] > ma_df['ma_{}'.format(self.window)]
        # return ma_df


if __name__ == '__main__':
    factor = CrossMaFactor(start_timestamp='2018-01-01', end_timestamp='2019-05-01')
    factor.run()
