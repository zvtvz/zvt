# -*- coding: utf-8 -*-
import argparse

import pandas as pd
from jqdatasdk import auth, logout, get_bars

from zvdata import IntervalLevel
from zvdata.api import df_to_db
from zvdata.recorder import FixedCycleDataRecorder
from zvdata.utils.pd_utils import pd_is_not_null
from zvdata.utils.time_utils import to_time_str, now_pd_timestamp, TIME_FORMAT_DAY, TIME_FORMAT_ISO8601
from zvt import init_log, zvt_env
from zvt.api.common import generate_kdata_id, get_kdata_schema
from zvt.api.quote import get_kdata
from zvt.domain import Stock, StockKdataCommon
from zvt.recorders.joinquant import to_jq_trading_level, to_jq_entity_id


class ChinaStockKdataRecorder(FixedCycleDataRecorder):
    # 复用eastmoney的股票列表
    entity_provider = 'eastmoney'
    entity_schema = Stock

    # 数据来自jq
    provider = 'joinquant'

    # 只是为了把recorder注册到data_schema
    data_schema = StockKdataCommon

    def __init__(self,
                 exchanges=['sh', 'sz'],
                 entity_ids=None,
                 codes=None,
                 batch_size=10,
                 force_update=True,
                 sleeping_time=10,
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
        self.data_schema = get_kdata_schema(entity_type='stock', level=level)
        self.jq_trading_level = to_jq_trading_level(level)

        super().__init__('stock', exchanges, entity_ids, codes, batch_size, force_update, sleeping_time,
                         default_size, real_time, fix_duplicate_way, start_timestamp, end_timestamp, close_hour,
                         close_minute, level, kdata_use_begin_time, one_day_trading_minutes)

        self.factor = 0
        self.last_timestamp = None

        auth(zvt_env['jq_username'], zvt_env['jq_password'])

    def generate_domain_id(self, entity, original_data):
        return generate_kdata_id(entity_id=entity.id, timestamp=original_data['timestamp'], level=self.level)

    def on_finish_entity(self, entity):
        # 重新计算前复权数据
        if self.factor != 0:
            kdatas = get_kdata(provider=self.provider, entity_id=entity.id, level=self.level.value,
                               order=self.data_schema.timestamp.asc(),
                               return_type='domain',
                               session=self.session,
                               filters=[self.data_schema.timestamp < self.last_timestamp])
            if kdatas:
                self.logger.info('recomputing {} qfq kdata,factor is:{}'.format(entity.code, self.factor))
                for kdata in kdatas:
                    kdata.open = round(kdata.open * self.factor, 2)
                    kdata.close = round(kdata.close * self.factor, 2)
                    kdata.high = round(kdata.high * self.factor, 2)
                    kdata.low = round(kdata.low * self.factor, 2)
                self.session.add_all(kdatas)
                self.session.commit()

    def on_finish(self):
        super().on_finish()
        logout()

    def record(self, entity, start, end, size, timestamps):
        # 只要前复权数据
        if not self.end_timestamp:
            df = get_bars(to_jq_entity_id(entity),
                          count=size,
                          unit=self.jq_trading_level,
                          fields=['date', 'open', 'close', 'low', 'high', 'volume', 'money'],
                          fq_ref_date=to_time_str(now_pd_timestamp()),
                          include_now=True)
        else:
            end_timestamp = to_time_str(self.end_timestamp)
            df = get_bars(to_jq_entity_id(entity),
                          count=size,
                          unit=self.jq_trading_level,
                          fields=['date', 'open', 'close', 'low', 'high', 'volume', 'money'],
                          end_dt=end_timestamp,
                          fq_ref_date=to_time_str(now_pd_timestamp()),
                          include_now=False)

        if pd_is_not_null(df):
            df['name'] = entity.name
            df.rename(columns={'money': 'turnover', 'date': 'timestamp'}, inplace=True)

            df['entity_id'] = entity.id
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df['provider'] = 'joinquant'
            df['level'] = self.level.value
            df['code'] = entity.code

            # 判断是否需要重新计算之前保存的前复权数据
            check_df = df.head(1)
            check_date = check_df['timestamp'][0]
            current_df = get_kdata(entity_id=entity.id, provider=self.provider, start_timestamp=check_date,
                                   end_timestamp=check_date, limit=1, level=self.level)
            if pd_is_not_null(current_df):
                old = current_df.iloc[0, :]['close']
                new = check_df['close'][0]
                # 相同时间的close不同，表明前复权需要重新计算
                if round(old, 2) != round(new, 2):
                    self.factor = new / old
                    self.last_timestamp = pd.Timestamp(check_date)

            def generate_kdata_id(se):
                if self.level >= IntervalLevel.LEVEL_1DAY:
                    return "{}_{}".format(se['entity_id'], to_time_str(se['timestamp'], fmt=TIME_FORMAT_DAY))
                else:
                    return "{}_{}".format(se['entity_id'], to_time_str(se['timestamp'], fmt=TIME_FORMAT_ISO8601))

            df['id'] = df[['entity_id', 'timestamp']].apply(generate_kdata_id, axis=1)

            df_to_db(df=df, data_schema=self.data_schema, provider=self.provider, force_update=self.force_update)

        return None


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--level', help='trading level', default='1d', choices=[item.value for item in IntervalLevel])
    parser.add_argument('--codes', help='codes', default=['000002'], nargs='+')

    args = parser.parse_args()

    level = IntervalLevel(args.level)
    codes = args.codes

    init_log('jq_china_stock_{}_kdata.log'.format(args.level))
    ChinaStockKdataRecorder(level=level, sleeping_time=0, codes=codes).run()
