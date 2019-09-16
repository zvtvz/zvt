# -*- coding: utf-8 -*-
import argparse

import pandas as pd
from jqdatasdk import auth, get_price, logout

from zvdata import IntervalLevel
from zvdata.recorder import FixedCycleDataRecorder
from zvdata.utils.pd_utils import df_is_not_null
from zvdata.utils.time_utils import to_time_str, now_time_str, to_pd_timestamp, now_pd_timestamp, TIME_FORMAT_MINUTE2
from zvdata.utils.utils import init_process_log
from zvt.api.common import generate_kdata_id, get_kdata_schema
from zvt.api.quote import get_kdata
from zvt.domain import Stock
from zvt.recorders.joinquant import to_jq_trading_level, to_jq_entity_id
from zvt.settings import JQ_ACCOUNT, JQ_PASSWD, SAMPLE_STOCK_CODES


class JQChinaStockKdataRecorder(FixedCycleDataRecorder):
    # 复用eastmoney的股票列表
    entity_provider = 'eastmoney'
    entity_schema = Stock

    # 数据来自jq
    provider = 'joinquant'

    def __init__(self,
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
                 level=IntervalLevel.LEVEL_1DAY,
                 kdata_use_begin_time=False,
                 close_hour=15,
                 close_minute=0,
                 one_day_trading_minutes=4 * 60) -> None:
        # 周线以上级别请使用jq_stock_bar_recorder
        assert level <= IntervalLevel.LEVEL_1DAY

        self.data_schema = get_kdata_schema(entity_type='stock', level=level)
        self.jq_trading_level = to_jq_trading_level(level)

        super().__init__('stock', ['sh', 'sz'], entity_ids, codes, batch_size, force_update, sleeping_time,
                         default_size, real_time, fix_duplicate_way, start_timestamp, end_timestamp, level,
                         kdata_use_begin_time, close_hour, close_minute, one_day_trading_minutes)

        # 读取已经保存的最新factor,更新时有变化才需要重新计算前复权价格
        self.current_factors = {}

        for security_item in self.entities:
            kdata = get_kdata(entity_id=security_item.id, provider=self.provider,
                              level=self.level.value, order=self.data_schema.timestamp.desc(),
                              limit=1,
                              return_type='domain',
                              session=self.session)
            if kdata:
                self.current_factors[security_item.id] = kdata[0].factor
                self.logger.info('{} latest factor:{}'.format(security_item.id, kdata[0].factor))

        auth(JQ_ACCOUNT, JQ_PASSWD)

    def generate_domain_id(self, entity, original_data):
        return generate_kdata_id(entity_id=entity.id, timestamp=original_data['timestamp'], level=self.level)

    def on_finish_entity(self, entity):
        kdatas = get_kdata(provider=self.provider, entity_id=entity.id, level=self.level.value,
                           order=self.data_schema.timestamp.asc(),
                           return_type='domain',
                           session=self.session,
                           filters=[self.data_schema.hfq_close.is_(None),
                                    self.data_schema.timestamp >= to_pd_timestamp('2005-01-01')])
        if kdatas:
            start = kdatas[0].timestamp
            end = kdatas[-1].timestamp

            # get hfq from joinquant
            df = get_price(to_jq_entity_id(entity), start_date=to_time_str(start), end_date=now_time_str(),
                           frequency='daily',
                           fields=['factor', 'open', 'close', 'low', 'high'],
                           skip_paused=True, fq='post')
            if df_is_not_null(df):
                # fill hfq data
                for kdata in kdatas:
                    time_str = to_time_str(kdata.timestamp)
                    if time_str in df.index:
                        kdata.hfq_open = df.loc[time_str, 'open']
                        kdata.hfq_close = df.loc[time_str, 'close']
                        kdata.hfq_high = df.loc[time_str, 'high']
                        kdata.hfq_low = df.loc[time_str, 'low']
                        kdata.factor = df.loc[time_str, 'factor']
                self.session.add_all(kdatas)
                self.session.commit()

                latest_factor = df.factor[-1]
                # factor not change yet, no need to reset the qfq past
                if latest_factor == self.current_factors.get(entity.id):
                    sql = 'UPDATE {} SET qfq_close=hfq_close/{},qfq_high=hfq_high/{}, qfq_open= hfq_open/{}, qfq_low= hfq_low/{} where ' \
                          'entity_id=\'{}\' and level=\'{}\' and (qfq_close isnull or qfq_high isnull or qfq_low isnull or qfq_open isnull)'.format(
                        self.data_schema.__table__, latest_factor, latest_factor, latest_factor, latest_factor,
                        entity.id, self.level.value)
                else:
                    sql = 'UPDATE {} SET qfq_close=hfq_close/{},qfq_high=hfq_high/{}, qfq_open= hfq_open/{}, qfq_low= hfq_low/{} where ' \
                          'entity_id=\'{}\' and level=\'{}\''.format(self.data_schema.__table__, latest_factor,
                                                                     latest_factor, latest_factor, latest_factor,
                                                                     entity.id,
                                                                     self.level.value)
                self.logger.info(sql)
                self.session.execute(sql)
                self.session.commit()

    def on_finish(self):
        super().on_finish()
        logout()

    def record(self, entity, start, end, size, timestamps):
        if self.start_timestamp:
            start = max(self.start_timestamp, to_pd_timestamp(start))

        end = now_pd_timestamp()

        start_timestamp = to_time_str(start)

        # 聚宽get_price函数必须指定结束时间，否则会有未来数据
        end_timestamp = to_time_str(end, fmt=TIME_FORMAT_MINUTE2)
        # 不复权
        df = get_price(to_jq_entity_id(entity), start_date=to_time_str(start_timestamp),
                       end_date=end_timestamp,
                       frequency=self.jq_trading_level,
                       fields=['open', 'close', 'low', 'high', 'volume', 'money'],
                       skip_paused=True, fq=None)
        df.index.name = 'timestamp'
        df.reset_index(inplace=True)
        df['name'] = entity.name
        df.rename(columns={'money': 'turnover'}, inplace=True)

        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df['provider'] = 'joinquant'
        df['level'] = self.level.value

        return df.to_dict(orient='records')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--level', help='trading level', default='1d', choices=[item.value for item in IntervalLevel])
    parser.add_argument('--codes', help='codes', default=SAMPLE_STOCK_CODES, nargs='+')

    args = parser.parse_args()

    level = IntervalLevel(args.level)
    codes = args.codes

    init_process_log('jq_china_stock_{}_kdata.log'.format(args.level))
    JQChinaStockKdataRecorder(level=level, sleeping_time=0, codes=codes).run()
