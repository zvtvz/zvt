# -*- coding: utf-8 -*-
import argparse

import pandas as pd
from jqdatasdk import auth, logout, get_factor_values

from zvt import init_log, zvt_env
from zvt.api.quote import get_stock_factor_schema
from zvt.contract import IntervalLevel
from zvt.contract.api import df_to_db
from zvt.contract.recorder import FixedCycleDataRecorder
from zvt.recorders.joinquant.common import to_jq_trading_level, to_jq_entity_id
from zvt.domain import Stock,StockFactorCommon
from zvt.utils.pd_utils import pd_is_not_null
from zvt.utils.time_utils import to_time_str, now_pd_timestamp, TIME_FORMAT_DAY, TIME_FORMAT_ISO8601


class JqChinaStockFactorRecorder(FixedCycleDataRecorder):
    entity_provider = 'joinquant'
    entity_schema = Stock
    data_schema = StockFactorCommon
    # 数据来自jq
    provider = 'joinquant'

    def __init__(self,
                 exchanges=['sh', 'sz'],
                 schema=None,
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
                 one_day_trading_minutes=4 * 60,
                 ) -> None:
        level = IntervalLevel(level)
        self.data_schema = get_stock_factor_schema(schema)
        self.jq_trading_level = to_jq_trading_level(level)

        super().__init__('stock', exchanges, entity_ids, codes, batch_size, force_update, sleeping_time,
                         default_size, real_time, fix_duplicate_way, start_timestamp, end_timestamp, close_hour,
                         close_minute, level, kdata_use_begin_time, one_day_trading_minutes)

        auth(zvt_env['jq_username'], zvt_env['jq_password'])

    def on_finish(self):
        super().on_finish()
        logout()

    def record(self, entity, start, end, size, timestamps):
        now_date = to_time_str(now_pd_timestamp())
        jq_entity_di = to_jq_entity_id(entity)
        if size > 1000:
            start_end_size = self.evaluate_start_end_size_timestamps(entity)
            size = 1000
            bdate= pd.bdate_range(start=start_end_size[0], periods=size)
            self.start_timestamp = bdate[0]
            self.end_timestamp = bdate[-1] if bdate[-1] <= now_pd_timestamp() else now_pd_timestamp()

        if not self.end_timestamp:
            factor_data = get_factor_values(securities=[jq_entity_di],
                                            factors=self.data_schema.important_cols(),
                                            end_date=now_date,
                                            count=size)
        else:
            end_timestamp = to_time_str(self.end_timestamp)
            if self.start_timestamp:
                start_timestamp = to_time_str(self.start_timestamp)
            else:
                bdate_list = pd.bdate_range(end=end_timestamp, periods=size)
                start_timestamp = to_time_str(bdate_list[0])

            factor_data = get_factor_values(securities=[to_jq_entity_id(entity)],
                                            factors=self.data_schema.important_cols(),
                                            start_date=start_timestamp,
                                            end_date=end_timestamp)
        df_list = [values.rename(columns={jq_entity_di: key}) for key, values in factor_data.items()]
        if len(df_list) != 0:
            df = pd.concat(df_list,join='inner',sort=True,axis=1).sort_index(ascending=True)
        else:
            df = pd.DataFrame(columns=self.data_schema.important_cols(),index=pd.bdate_range(start=start_timestamp,end=end_timestamp))
        if pd_is_not_null(df):
            df_fill = pd.DataFrame(index=pd.bdate_range(start=start_timestamp, end=end_timestamp)) if self.end_timestamp else pd.DataFrame(index=df.index)
            if df_fill.shape[0] != df.shape[0]:
                df = pd.concat([df_fill,df],axis=1)
            df['name'] = entity.name
            df['entity_id'] = entity.id
            df['timestamp'] = pd.to_datetime(df.index)
            df['provider'] = 'joinquant'
            df['code'] = entity.code
            def generate_factor_id(se):
                if self.level >= IntervalLevel.LEVEL_1DAY:
                    return "{}_{}".format(se['entity_id'], to_time_str(se['timestamp'], fmt=TIME_FORMAT_DAY))
                else:
                    return "{}_{}".format(se['entity_id'], to_time_str(se['timestamp'], fmt=TIME_FORMAT_ISO8601))
            df['id'] = df[['entity_id', 'timestamp']].apply(generate_factor_id, axis=1)

        df_to_db(df=df, data_schema=self.data_schema, provider=self.provider, force_update=self.force_update)

        return None


__all__ = ['JqChinaStockFactorRecorder']

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--level', help='trading level', default='1d', choices=[item.value for item in IntervalLevel])
    parser.add_argument('--codes', help='codes', default=['000001'], nargs='+')


    args = parser.parse_args()

    level = IntervalLevel(args.level)
    codes = args.codes

    init_log('jq_china_stock_{}_kdata.log'.format(args.level))
    JqChinaStockFactorRecorder(level=level, sleeping_time=0, codes=codes, real_time=False, ).run()
    #
    # print(get_kdata(entity_id='stock_sz_000001', limit=10, order=StockFactor.timestamp.desc(),
    #                 adjust_type=AdjustType.hfq))
