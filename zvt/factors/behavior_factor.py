# -*- coding: utf-8 -*-
import pandas as pd

from zvt.domain import SecurityType, ManagerTrading
from zvt.factors.factor import OneSchemaMustFactor


class ManagerGiveUpFactor(OneSchemaMustFactor):
    data_schema = ManagerTrading

    def __init__(self, security_type=SecurityType.stock, exchanges=['sh', 'sz'], codes=None, the_timestamp=None,
                 window=None, window_func='mean', start_timestamp=None, end_timestamp=None,
                 columns=[ManagerTrading.volume], filters=[ManagerTrading.trading_way == '减持'],
                 provider='eastmoney') -> None:
        super().__init__(security_type, exchanges, codes, the_timestamp, window, window_func, start_timestamp,
                         end_timestamp, columns, filters, provider=provider)

    def run(self):
        self.df = self.data_df.copy()
        self.df['score'] = False
        print(self.df)


if __name__ == '__main__':
    factor = ManagerGiveUpFactor(the_timestamp='2017-12-31', window=pd.DateOffset(days=365))
    factor.run()
