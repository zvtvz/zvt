# -*- coding: utf-8 -*-
import pandas as pd
from jqdatasdk import auth, get_query_count, query,finance

from zvt import zvt_env
from zvt.api import AdjustType, TIME_FORMAT_DAY, TIME_FORMAT_ISO8601, get_str_schema
from zvt.contract import IntervalLevel
from zvt.contract.api import df_to_db
from zvt.contract.recorder import FixedCycleDataRecorder
from zvt.recorders.joinquant.common import to_jq_trading_level
from zvt.utils.pd_utils import pd_is_not_null
from zvt.utils.time_utils import now_pd_timestamp, to_time_str
from zvt.domain import FundNetValueCommon,Fund


class JqEtfNetValueRecorder(FixedCycleDataRecorder):
    """
    记录公募基金的净值数据
    """
    entity_provider = 'joinquant'
    entity_schema = Fund

    # 数据来自jq
    provider = 'joinquant'

    data_schema = FundNetValueCommon

    def __init__(self,
                 entity_type='fund',
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
                 level=IntervalLevel.LEVEL_1DAY,
                 kdata_use_begin_time=False,
                 close_hour=15,
                 close_minute=0,
                 one_day_trading_minutes=4 * 60,
                 ) -> None:

        level = IntervalLevel(level)

        self.data_schema = get_str_schema('FundNetValue')
        self.jq_trading_level = to_jq_trading_level(level)

        super().__init__('fund', exchanges, entity_ids, codes, batch_size, force_update, sleeping_time,
                         default_size, real_time, fix_duplicate_way, start_timestamp, end_timestamp, close_hour,
                         close_minute, level, kdata_use_begin_time, one_day_trading_minutes)

        auth(zvt_env['jq_username'], zvt_env['jq_password'])
        print(f"剩余{get_query_count()['spare'] / 10000}万")


    def record(self, entity, start, end, size, timestamps):

        df = finance.run_query(query(finance.FUND_NET_VALUE).filter(finance.FUND_NET_VALUE.code == entity.code).filter(
            finance.FUND_NET_VALUE.day >= to_time_str(start)))

        if pd_is_not_null(df):
            df.reset_index(inplace=True,drop=True)
            df['name'] = entity.name
            df.rename(columns={'day': 'timestamp'}, inplace=True)
            df['entity_id'] = entity.id
            df['timestamp'] = pd.to_datetime(df.timestamp)
            df['provider'] = 'joinquant'
            df['level'] = self.level.value
            df['code'] = entity.code

            def generate_kdata_id(se):
                if self.level >= IntervalLevel.LEVEL_1DAY:
                    return "{}_{}".format(se['entity_id'], to_time_str(se['timestamp'], fmt=TIME_FORMAT_DAY))
                else:
                    return "{}_{}".format(se['entity_id'], to_time_str(se['timestamp'], fmt=TIME_FORMAT_ISO8601))

            df['id'] = df[['entity_id', 'timestamp']].apply(generate_kdata_id, axis=1)
            df_to_db(df=df, data_schema=self.data_schema, provider=self.provider, force_update=self.force_update)
        return None


__all__ = ['JqEtfNetValueRecorder']

if __name__ == '__main__':
    # 上证50
    JqEtfNetValueRecorder(codes=['050002']).run()
    # JqChinaEtfValuationRecorder(codes=['512290']).run()
