# -*- coding: utf-8 -*-
import pandas as pd

from zvt.api.common import get_data
from zvt.domain import TradingLevel, FinanceFactor
from zvt.utils.pd_utils import index_df_with_security_time
from zvt.utils.time_utils import now_pd_timestamp


def ma_statistic(security_type, timestamp, trading_level=TradingLevel.LEVEL_1DAY, ma_args=[5, 10, 30, 120, 250],
                 return_securities=False):
    """

    :param trading_level:
    :type trading_level:
    :param security_type:
    :type security_type:
    :param timestamp:
    :type timestamp:
    :param ma_args:
    :type ma_args:
    :param return_securities:
    :type return_securities:

    """
    pass


def finance_score(data_schema, security_id=None, codes=None, provider='eastmoney', fields=None,
                  timestamp=now_pd_timestamp(), report_count=20):
    fields = fields + ['security_id', 'timestamp', 'report_date']

    data_df = get_data(data_schema=data_schema, security_id=security_id, codes=codes, provider=provider, columns=fields,
                       end_timestamp=timestamp)

    time_series = data_df['report_date'].drop_duplicates()
    time_series = time_series[-report_count:]

    data_df = index_df_with_security_time(data_df)

    idx = pd.IndexSlice

    df = data_df.loc[idx[:, time_series],]
    print(df)

    df = df.groupby(df['security_id']).mean()
    print(df)

    quantile = df.quantile([0.1, 0.3, 0.5, 0.7, 0.9])

    def evaluate_score(s, column):
        the_column = column
        if s > quantile.loc[0.9, the_column]:
            return 0.9
        if s > quantile.loc[0.7, the_column]:
            return 0.7
        if s > quantile.loc[0.5, the_column]:
            return 0.5
        if s > quantile.loc[0.3, the_column]:
            return 0.3
        if s > quantile.loc[0.1, the_column]:
            return 0.1
        return 0

    for item in quantile.columns:
        df[item] = df[item].apply(lambda x: evaluate_score(x, item))

    print(df)


if __name__ == '__main__':
    print(type(FinanceFactor.op_income_growth_yoy))
    print(FinanceFactor.op_income_growth_yoy.key)
    # print(
    #     finance_score(FinanceFactor, fields=[FinanceFactor.op_income_growth_yoy.key, FinanceFactor.net_profit_growth_yoy]))
