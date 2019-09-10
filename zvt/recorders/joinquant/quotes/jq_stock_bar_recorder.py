# -*- coding: utf-8 -*-
import argparse

import pandas as pd
from jqdatasdk import auth, logout, get_bars

from zvdata import IntervalLevel
from zvdata.recorder import FixedCycleDataRecorder
from zvdata.utils.pd_utils import df_is_not_null
from zvdata.utils.time_utils import to_time_str, now_pd_timestamp
from zvdata.utils.utils import init_process_log
from zvt.api.common import generate_kdata_id, get_kdata_schema
from zvt.api.quote import get_kdata
from zvt.domain import Stock
from zvt.recorders.joinquant import to_jq_trading_level, to_jq_entity_id
from zvt.settings import JQ_ACCOUNT, JQ_PASSWD


class JQChinaStockBarRecorder(FixedCycleDataRecorder):
    # 复用eastmoney的股票列表
    entity_provider = 'eastmoney'
    entity_schema = Stock

    # 数据来自jq
    provider = 'joinquant'

    def __init__(self,
                 entity_ids=None,
                 codes=None,
                 batch_size=10,
                 force_update=False,
                 sleeping_time=5,
                 default_size=2000,
                 one_shot=True,
                 fix_duplicate_way='ignore',
                 start_timestamp=None,
                 end_timestamp=None,
                 contain_unfinished_data=False,
                 level=IntervalLevel.LEVEL_1WEEK,
                 kdata_use_begin_time=False,
                 close_hour=15,
                 close_minute=0,
                 one_day_trading_minutes=4 * 60) -> None:
        # 周线以上级别
        assert level >= IntervalLevel.LEVEL_1WEEK

        self.data_schema = get_kdata_schema(entity_type='stock', level=level)
        self.jq_trading_level = to_jq_trading_level(level)

        super().__init__('stock', ['sh', 'sz'], entity_ids, codes, batch_size, force_update, sleeping_time,
                         default_size, one_shot, fix_duplicate_way, start_timestamp, end_timestamp,
                         contain_unfinished_data, level, kdata_use_begin_time, close_hour, close_minute,
                         one_day_trading_minutes)
        self.factor = 0
        self.last_timestamp = None

        auth(JQ_ACCOUNT, JQ_PASSWD)

    def generate_domain_id(self, entity, original_data):
        return generate_kdata_id(entity_id=entity.id, timestamp=original_data['timestamp'], level=self.level)

    def on_finish_entity(self, entity):
        if self.factor != 0:
            kdatas = get_kdata(provider=self.provider, entity_id=entity.id, level=self.level.value,
                               order=self.data_schema.timestamp.asc(),
                               return_type='domain',
                               session=self.session,
                               filters=[self.data_schema.timestamp <= self.last_timestamp])
            if kdatas:
                # fill hfq data
                for kdata in kdatas:
                    kdata.qfq_open = kdata.qfq_open * self.factor
                    kdata.qfq_close = kdata.qfq_close * self.factor
                    kdata.qfq_high = kdata.qfq_high * self.factor
                    kdata.qfq_low = kdata.qfq_low * self.factor
                self.session.commit()

    def on_finish(self):
        super().on_finish()
        logout()

    def record(self, entity, start, end, size, timestamps):
        # 不复权
        df = get_bars(to_jq_entity_id(entity),
                      count=size,
                      unit=self.jq_trading_level,
                      fields=['date', 'open', 'close', 'low', 'high', 'volume', 'money'],
                      fq_ref_date=None,
                      include_now=False)
        df['name'] = entity.name
        df.rename(columns={'money': 'turnover'}, inplace=True)

        df['timestamp'] = pd.to_datetime(df['date'])
        df['provider'] = 'joinquant'
        df['level'] = self.level.value

        # 前复权
        end_timestamp = to_time_str(now_pd_timestamp())
        qfq_df = get_bars(to_jq_entity_id(entity),
                          count=size,
                          unit=self.jq_trading_level,
                          fields=['date', 'open', 'close', 'low', 'high'],
                          fq_ref_date=end_timestamp,
                          include_now=False)
        # not need to update past
        df['qfq_close'] = qfq_df['close']
        df['qfq_open'] = qfq_df['open']
        df['qfq_high'] = qfq_df['high']
        df['qfq_low'] = qfq_df['low']

        check_df = qfq_df.head(1)
        check_date = check_df['date'][0]

        current_df = get_kdata(entity_id=entity.id, provider=self.provider, start_timestamp=check_date,
                               end_timestamp=check_date, limit=1, level=self.level)

        if df_is_not_null(current_df):
            c1 = current_df.iloc[0, :]['qfq_close']
            c2 = check_df['close'][0]
            if c1 != c2:
                self.factor = c2 / c1
                self.last_timestamp = check_date

        return df.to_dict(orient='records')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--level', help='trading level', default='1wk', choices=[item.value for item in IntervalLevel])
    parser.add_argument('--codes', help='codes', default=['000338', '000001'], nargs='+')

    args = parser.parse_args()

    level = IntervalLevel(args.level)
    codes = args.codes

    init_process_log('jq_china_stock_{}_kdata.log'.format(args.level))
    JQChinaStockBarRecorder(level=level, sleeping_time=0, codes=codes).run()
