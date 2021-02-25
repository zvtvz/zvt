# -*- coding: utf-8 -*-
from jqdatasdk import auth, get_query_count, finance, query, get_locked_shares
import pandas as pd
from zvt.recorders.joinquant.common import to_jq_entity_id
from datetime import timedelta
from zvt import zvt_env
from zvt.api import get_str_schema, to_time_str, pd_is_not_null, TIME_FORMAT_DAY,now_pd_timestamp
from zvt.contract.api import df_to_db
from zvt.contract.recorder import FixedCycleDataRecorder
from zvt.domain import LockedShares
from zvt.domain import Stock


class LockedSharesRecorder(FixedCycleDataRecorder):
    """
    限售股
    """
    entity_provider = 'joinquant'
    entity_schema = Stock

    # 数据来自jq
    provider = 'joinquant'

    data_schema = LockedShares

    def __init__(self,
                 entity_type='stock',
                 exchanges=['sh', 'sz'],
                 entity_ids=None,
                 codes=None,
                 batch_size=10,
                 force_update=True,
                 sleeping_time=0,
                 default_size=2000,
                 real_time=False,
                 fix_duplicate_way='ignore',
                 start_timestamp=None,
                 end_timestamp=None,
                 kdata_use_begin_time=False,
                 level=None,
                 close_hour=15,
                 close_minute=0,
                 one_day_trading_minutes=4 * 60,
                 ) -> None:
        self.data_schema = get_str_schema('LockedShares')

        super().__init__('fund', exchanges, entity_ids, codes, batch_size, force_update, sleeping_time,
                         default_size, real_time, fix_duplicate_way, start_timestamp, end_timestamp, close_hour,
                         close_minute, level, kdata_use_begin_time, one_day_trading_minutes)

        auth(zvt_env['jq_username'], zvt_env['jq_password'])
        print(f"剩余{get_query_count()['spare'] / 10000}万")

    def record(self, entity, start, end, size, timestamps):
        df = get_locked_shares([to_jq_entity_id(entity)],
                               start_date=to_time_str(start),
                               end_date=to_time_str(now_pd_timestamp() + timedelta(days=150))
                               )


        if pd_is_not_null(df):

            df['locked_rate1'] = df['rate1'] * 100
            df['locked_rate2'] = df['rate2'] * 100
            df['locked_num'] = df['num']

            df['entity_id'] = entity.id
            df['end_date'] = pd.to_datetime(df.day)

            df['timestamp'] = df['end_date']
            df['provider'] = 'joinquant'
            df['code'] = entity.code

            def generate_id(se):
                return "{}_{}".format(se['entity_id'], to_time_str(se['timestamp'], fmt=TIME_FORMAT_DAY))

            df['id'] = df[['entity_id', 'timestamp']].apply(generate_id, axis=1)

            df_to_db(df=df, data_schema=self.data_schema, provider=self.provider, force_update=self.force_update)
        return None


__all__ = ['LockedSharesRecorder']

if __name__ == '__main__':
    # init_log('holder_trading.log')

    recorder = LockedSharesRecorder(codes=['002572'])
    recorder.run()
