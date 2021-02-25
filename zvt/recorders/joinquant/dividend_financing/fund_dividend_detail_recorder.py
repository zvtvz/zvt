# -*- coding: utf-8 -*-
import pandas as pd

from zvt import zvt_env
from zvt.api import TIME_FORMAT_DAY, get_str_schema
from zvt.contract.api import df_to_db
from zvt.contract.recorder import TimeSeriesDataRecorder
from zvt.domain import Fund,FundDividendDetail
from zvt.utils.pd_utils import pd_is_not_null
from zvt.utils.time_utils import now_pd_timestamp, to_time_str
from jqdatasdk import auth, query, indicator, get_fundamentals, logout, finance

class JqDividendDetailRecorder(TimeSeriesDataRecorder):
    entity_provider = 'joinquant'
    entity_schema = Fund
    provider = 'joinquant'

    data_schema = FundDividendDetail

    def __init__(self, entity_type='stock', exchanges=['sh', 'sz'], entity_ids=None, codes=None, batch_size=10,
                 force_update=False, sleeping_time=5, default_size=2000, real_time=False,
                 fix_duplicate_way='add', start_timestamp=None, end_timestamp=None, close_hour=0,
                 close_minute=0) -> None:
        self.data_schema = get_str_schema('FundDividendDetail')
        super().__init__(entity_type, exchanges, entity_ids, codes, batch_size, force_update, sleeping_time,
                         default_size, real_time, fix_duplicate_way, start_timestamp, end_timestamp, close_hour,
                         close_minute)
        auth(zvt_env['jq_username'], zvt_env['jq_password'])

    def on_finish(self):
        logout()

    def record(self, entity, start, end, size, timestamps):
        if not end:
            end = to_time_str(now_pd_timestamp())
        start = to_time_str(start)

        df = finance.run_query(query(
            finance.FUND_DIVIDEND).filter(
            finance.FUND_DIVIDEND.code == entity.code,finance.FUND_DIVIDEND.pub_date >= start).limit(20))
        df.rename(columns=FundDividendDetail.get_data_map(self), inplace=True)
        df.dropna(subset=['dividend_date'], inplace=True)
        if pd_is_not_null(df):
            df.reset_index(drop=True,inplace=True)
            df['entity_id'] = entity.id
            df['timestamp'] = pd.to_datetime(df.announce_date)
            df['provider'] = 'joinquant'
            df['code'] = entity.code

            def generate_id(se):
                return "{}_{}_{}".format(se['entity_id'], to_time_str(se['timestamp'], fmt=TIME_FORMAT_DAY), se.name)
            df.reset_index(drop=True,inplace=True)
            df.index += 1
            df['id'] = df[['entity_id', 'timestamp']].apply(generate_id, axis=1)

            df['id'] = df[['entity_id', 'timestamp']].apply(generate_id, axis=1)
            df_to_db(df=df, data_schema=self.data_schema, provider=self.provider, force_update=self.force_update)
        return None


__all__ = ['JqDividendDetailRecorder']

if __name__ == '__main__':
    # 上证50
    JqDividendDetailRecorder(codes=['050002']).run()
    # JqChinaEtfValuationRecorder(codes=['512290']).run()
