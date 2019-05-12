import pandas as pd

from zvt.api.common import get_kdata_schema
from zvt.domain import SecurityType, StockDayKdata
from zvt.factors.factor import OneSchemaMustFactor


class CrossMaFactor(OneSchemaMustFactor):
    def __init__(self, security_type=SecurityType.stock, exchanges=['sh', 'sz'], codes=None, the_timestamp=None,
                 window=None, window_func='mean', start_timestamp=None, end_timestamp=None,
                 columns=[StockDayKdata.qfq_close],
                 filters=None,
                 provider='netease') -> None:
        self.data_schema = get_kdata_schema(security_type)

        super().__init__(security_type, exchanges, codes, the_timestamp, window, window_func, start_timestamp,
                         end_timestamp, columns, filters, provider)

    def run(self):
        self.df = self.original_df.loc[self.data_df.index, :] > self.data_df
        print(self.df)


if __name__ == '__main__':
    factor = CrossMaFactor(start_timestamp='2018-01-01', end_timestamp='2019-05-01', window=pd.DateOffset(days=30))
    factor.run()
