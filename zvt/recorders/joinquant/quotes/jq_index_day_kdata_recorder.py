# -*- coding: utf-8 -*-
import time

import pandas as pd
from jqdatasdk import auth, get_price,normalize_code,get_query_count,get_bars

from zvt import zvt_env
from zvt.api import get_kdata_schema
from zvt.contract import IntervalLevel
from zvt.contract.api import df_to_db
from zvt.contract.recorder import FixedCycleDataRecorder
from zvt.recorders.joinquant.common import to_jq_trading_level

from zvt.utils.time_utils import to_time_str, now_pd_timestamp, TIME_FORMAT_DAY, TIME_FORMAT_ISO8601

from zvt.domain import Index, IndexKdataCommon


class ChinaIndexDayKdataRecorder(FixedCycleDataRecorder):
    entity_provider = 'joinquant'
    entity_schema = Index

    provider = 'joinquant'
    data_schema = IndexKdataCommon
    def __init__(self,
                 entity_type='index',
                 exchanges=['cn'],
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
                 level=IntervalLevel.LEVEL_1WEEK,
                 kdata_use_begin_time=False,
                 close_hour=15,
                 close_minute=0,
                 one_day_trading_minutes=4 * 60) -> None:

        level = IntervalLevel(level)
        self.jq_trading_level = to_jq_trading_level(level)
        self.data_schema = get_kdata_schema(entity_type=entity_type, level=level)


        super().__init__('stock', exchanges, entity_ids, codes, batch_size, force_update, sleeping_time,
                         default_size, real_time, fix_duplicate_way, start_timestamp, end_timestamp, close_hour,
                         close_minute, level, kdata_use_begin_time, one_day_trading_minutes)

        auth(zvt_env['jq_username'], zvt_env['jq_password'])

    def record(self, entity, start, end, size, timestamps):

        now_date = to_time_str(now_pd_timestamp())
        security = entity.id[-6:] + '.XSHG' if entity.name == '上证指数' else entity.id[-6:] + '.XSHE'
        try:
            if not self.end_timestamp:
                df = get_bars(security,
                              count=size,
                              unit=self.jq_trading_level,
                              fields=['date', 'open', 'close', 'low', 'high', 'volume', 'money'],
                              fq_ref_date=None,
                              include_now=self.real_time)
            else:
                end_timestamp = to_time_str(now_date)
                df = get_bars(security,
                              count=size,
                              unit=self.jq_trading_level,
                              fields=['date', 'open', 'close', 'low', 'high', 'volume', 'money'],
                              end_dt=end_timestamp,
                              fq_ref_date=None,
                              include_now=self.real_time)
        except Exception:
            print(f"找不到标的{security},{entity.name}")
            return None
        df.rename(columns={'money': 'turnover', 'date': 'timestamp'}, inplace=True)
        df['level'] = self.level.value
        df['entity_id'] = entity.id.replace('cn',security[-4:]).replace('XSHG','sh').replace('XSHE','sz')
        df['code'] = entity.id[-6:]
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df['provider'] = self.provider
        df['name'] = entity.name


        def generate_kdata_id(se):
            if self.level >= IntervalLevel.LEVEL_1DAY:
                return "{}_{}".format(se['entity_id'], to_time_str(se['timestamp'], fmt=TIME_FORMAT_DAY))
            else:
                return "{}_{}".format(se['entity_id'], to_time_str(se['timestamp'], fmt=TIME_FORMAT_ISO8601))

        df['id'] = df[['entity_id', 'timestamp']].apply(generate_kdata_id, axis=1)

        df_to_db(df=df, data_schema=self.data_schema, provider=self.provider, force_update=self.force_update)
        return None

__all__ = ['ChinaIndexDayKdataRecorder']

if __name__ == '__main__':
    ChinaIndexDayKdataRecorder(sleeping_time=1).run()
