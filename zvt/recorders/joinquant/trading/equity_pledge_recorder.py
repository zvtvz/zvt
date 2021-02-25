# -*- coding: utf-8 -*-
from jqdatasdk import auth, get_query_count, finance, query
import pandas as pd
from zvt.recorders.joinquant.common import to_jq_entity_id

from zvt import zvt_env
from zvt.api import get_str_schema, to_time_str, pd_is_not_null, TIME_FORMAT_DAY
from zvt.contract.api import df_to_db
from zvt.contract.recorder import FixedCycleDataRecorder
from zvt.domain import EquityPledge
from zvt.domain import Stock


class EquityPledgeRecorder(FixedCycleDataRecorder):
    """
    股权质押
    """
    entity_provider = 'joinquant'
    entity_schema = Stock

    # 数据来自jq
    provider = 'joinquant'

    data_schema = EquityPledge

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
        self.data_schema = get_str_schema('EquityPledge')

        super().__init__('fund', exchanges, entity_ids, codes, batch_size, force_update, sleeping_time,
                         default_size, real_time, fix_duplicate_way, start_timestamp, end_timestamp, close_hour,
                         close_minute, level, kdata_use_begin_time, one_day_trading_minutes)

        auth(zvt_env['jq_username'], zvt_env['jq_password'])
        print(f"剩余{get_query_count()['spare'] / 10000}万")

    def record(self, entity, start, end, size, timestamps):
        df = finance.run_query(query(finance.STK_SHARES_PLEDGE).filter(
            finance.STK_SHARES_PLEDGE.code == to_jq_entity_id(entity)).filter(
            finance.STK_SHARES_PLEDGE.pub_date >= to_time_str(start)))

        if pd_is_not_null(df):
            df['name'] = entity.name
            df['entity_id'] = entity.id
            df['pub_date'] = pd.to_datetime(df.pub_date)

            df['timestamp'] = df['pub_date']
            df['provider'] = 'joinquant'
            df['code'] = entity.code

            def generate_id(se):
                return "{}_{}_{}".format(se['entity_id'], to_time_str(se['timestamp'], fmt=TIME_FORMAT_DAY), se.name)

            df = pd.concat([i.reset_index(drop=True) for i in dict(list(df.groupby('timestamp'))).values()])
            df.index += 1
            df['id'] = df[['entity_id', 'timestamp']].apply(generate_id, axis=1)

            df_to_db(df=df, data_schema=self.data_schema, provider=self.provider, force_update=self.force_update)
        return None


__all__ = ['EquityPledgeRecorder']

if __name__ == '__main__':
    # init_log('holder_trading.log')

    recorder = EquityPledgeRecorder(codes=['002572'])
    recorder.run()
