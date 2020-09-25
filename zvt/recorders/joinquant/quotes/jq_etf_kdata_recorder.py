# -*- coding: utf-8 -*-
import pandas as pd
from jqdatasdk import get_price, normalize_code, auth,get_query_count

from zvt import zvt_env
from zvt.api import AdjustType, get_kdata_schema, get_kdata, TIME_FORMAT_DAY, TIME_FORMAT_ISO8601
from zvt.contract import IntervalLevel
from zvt.contract.api import df_to_db
from zvt.contract.recorder import TimeSeriesDataRecorder,FixedCycleDataRecorder
from zvt.recorders.joinquant.common import to_jq_trading_level
from zvt.utils.pd_utils import pd_is_not_null
from zvt.utils.time_utils import now_pd_timestamp, to_time_str
from zvt.api.quote import get_etf_stocks
from zvt.domain import StockValuation, Etf, EtfKdataCommon


class JqChinaEtfValuationRecorder(FixedCycleDataRecorder):
    entity_provider = 'joinquant'
    entity_schema = Etf

    # 数据来自jq
    provider = 'joinquant'

    data_schema = EtfKdataCommon
    def __init__(self,
                 entity_type='etf',
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
                 level=IntervalLevel.LEVEL_1WEEK,
                 kdata_use_begin_time=False,
                 close_hour=15,
                 close_minute=0,
                 one_day_trading_minutes=4 * 60,
                 adjust_type=AdjustType.qfq) -> None:

        level = IntervalLevel(level)
        adjust_type = AdjustType(adjust_type)
        self.data_schema = get_kdata_schema(entity_type=entity_type, level=level, adjust_type=adjust_type)
        self.jq_trading_level = to_jq_trading_level(level)

        super().__init__('stock', exchanges, entity_ids, codes, batch_size, force_update, sleeping_time,
                         default_size, real_time, fix_duplicate_way, start_timestamp, end_timestamp, close_hour,
                         close_minute, level, kdata_use_begin_time, one_day_trading_minutes)
        self.adjust_type = adjust_type
        auth(zvt_env['jq_username'], zvt_env['jq_password'])
        print(f"剩余{get_query_count()['spare']/10000}万")

    def recompute_qfq(self, entity, qfq_factor, last_timestamp):
        # 重新计算前复权数据
        if qfq_factor != 0:
            kdatas = get_kdata(provider=self.provider, entity_id=entity.id, level=self.level.value,
                               order=self.data_schema.timestamp.asc(),
                               return_type='domain',
                               session=self.session,
                               filters=[self.data_schema.timestamp < last_timestamp])
            if kdatas:
                self.logger.info('recomputing {} qfq kdata,factor is:{}'.format(entity.code, qfq_factor))
                for kdata in kdatas:
                    kdata.open = round(kdata.open * qfq_factor, 2)
                    kdata.close = round(kdata.close * qfq_factor, 2)
                    kdata.high = round(kdata.high * qfq_factor, 2)
                    kdata.low = round(kdata.low * qfq_factor, 2)
                self.session.add_all(kdatas)
                self.session.commit()

    def record(self, entity, start, end, size, timestamps):
        if not end:
            end = to_time_str(now_pd_timestamp())

        fq = fq_ref_date = None
        if self.adjust_type == AdjustType.hfq:
            fq = 'post'
            fq_ref_date = '2000-01-01'

        elif self.adjust_type == AdjustType.qfq:
            fq = 'pre'
            fq_ref_date = to_time_str(now_pd_timestamp())

        security = normalize_code(entity.code)
        if not self.end_timestamp:
            df = get_price(security,
                           start_date=start,
                           end_date=end,
                           frequency=self.jq_trading_level,
                           fields=['open', 'close', 'low', 'high', 'volume', 'money'],
                           fq=fq)
        else:
            end_timestamp = to_time_str(self.end_timestamp)
            df = get_price(security,
                           count=size,
                           frequency=self.jq_trading_level,
                           fields=['open', 'close', 'low', 'high', 'volume', 'money'],
                           end_date=end_timestamp,
                           fq=fq)

        if pd_is_not_null(df):
            df['name'] = entity.name
            df.index.name = 'timestamp'
            df.rename(columns={'money': 'turnover', 'date': 'timestamp'}, inplace=True)

            df['entity_id'] = entity.id
            df['timestamp'] = pd.to_datetime(df.index)
            df['provider'] = 'joinquant'
            df['level'] = self.level.value
            df['code'] = entity.code

            # 判断是否需要重新计算之前保存的前复权数据
            if self.adjust_type == AdjustType.qfq and df.open.dropna().shape[0] != 0:
                check_df = df.head(1)
                check_date = check_df['timestamp'][0]
                current_df = get_kdata(entity_id=entity.id, provider=self.provider, start_timestamp=check_date,
                                       end_timestamp=check_date, limit=1, level=self.level,
                                       adjust_type=self.adjust_type)
                if pd_is_not_null(current_df):
                    old = current_df.iloc[0, :]['close']
                    new = check_df['close'][0]
                    # 相同时间的close不同，表明前复权需要重新计算
                    if round(old, 2) != round(new, 2):
                        qfq_factor = new / old
                        last_timestamp = pd.Timestamp(check_date)
                        self.recompute_qfq(entity, qfq_factor=qfq_factor, last_timestamp=last_timestamp)

            def generate_kdata_id(se):
                if self.level >= IntervalLevel.LEVEL_1DAY:
                    return "{}_{}".format(se['entity_id'], to_time_str(se['timestamp'], fmt=TIME_FORMAT_DAY))
                else:
                    return "{}_{}".format(se['entity_id'], to_time_str(se['timestamp'], fmt=TIME_FORMAT_ISO8601))

            df['id'] = df[['entity_id', 'timestamp']].apply(generate_kdata_id, axis=1)
            df_to_db(df=df, data_schema=self.data_schema, provider=self.provider, force_update=self.force_update)
        return None


__all__ = ['JqChinaEtfValuationRecorder']

if __name__ == '__main__':
    # 上证50
    JqChinaEtfValuationRecorder(codes=['050002']).run()
    # JqChinaEtfValuationRecorder(codes=['512290']).run()
