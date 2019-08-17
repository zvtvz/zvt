# -*- coding: utf-8 -*-
import io

import pandas as pd
import requests
from jqdatasdk import auth, get_price, logout

from zvdata.recorder import FixedCycleDataRecorder
from zvdata.structs import IntervalLevel
from zvt.api.common import generate_kdata_id, to_jq_entity_id
from zvt.api.technical import get_kdata
from zvt.domain import Stock1dKdata, Stock
from zvt.settings import JQ_ACCOUNT, JQ_PASSWD
from zvt.utils import utils
from zvt.utils.time_utils import to_time_str, TIME_FORMAT_DAY1, now_time_str, to_pd_timestamp


class ChinaStockDayKdataRecorder(FixedCycleDataRecorder):
    entity_provider = 'eastmoney'
    entity_schema = Stock

    provider = 'netease'
    data_schema = Stock1dKdata
    url = 'http://quotes.money.163.com/service/chddata.html?code={}{}&start={}&end={}&fields=TCLOSE;HIGH;LOW;TOPEN;LCLOSE;CHG;PCHG;TURNOVER;VOTURNOVER;VATURNOVER'

    def __init__(self, entity_type='stock', exchanges=['sh', 'sz'], entity_ids=None, codes=None, batch_size=10,
                 force_update=False, sleeping_time=10, default_size=2000, one_shot=True, fix_duplicate_way='add',
                 start_timestamp=None, end_timestamp=None, contain_unfinished_data=False,
                 level=IntervalLevel.LEVEL_1DAY, kdata_use_begin_time=False, close_hour=0, close_minute=0,
                 one_day_trading_minutes=24 * 60) -> None:

        super().__init__(entity_type, exchanges, entity_ids, codes, batch_size, force_update, sleeping_time,
                         default_size, one_shot, fix_duplicate_way, start_timestamp, end_timestamp,
                         contain_unfinished_data, level, kdata_use_begin_time, close_hour, close_minute,
                         one_day_trading_minutes)

        self.current_factors = {}
        for security_item in self.entities:
            kdata = get_kdata(entity_id=security_item.id, provider=self.provider,
                              level=self.level.value, order=Stock1dKdata.timestamp.desc(),
                              limit=1,
                              return_type='domain',
                              session=self.session)
            if kdata:
                self.current_factors[security_item.id] = kdata[0].factor
                self.logger.info('{} latest factor:{}'.format(security_item.id, kdata[0].factor))

        auth(JQ_ACCOUNT, JQ_PASSWD)

    def get_data_map(self):
        return {}

    def generate_domain_id(self, entity, original_data):
        return generate_kdata_id(entity_id=entity.id, timestamp=original_data['timestamp'], level=self.level)

    def generate_request_param(self, security_item, start, end, size, timestamp):
        return {
            'security_item': security_item,
            'start': to_time_str(start, fmt=TIME_FORMAT_DAY1),
            'end': now_time_str(fmt=TIME_FORMAT_DAY1),
            'level': self.level.value
        }

    def on_finish_entity(self, entity):
        kdatas = get_kdata(entity_id=entity.id, level=self.level.value, order=Stock1dKdata.timestamp.asc(),
                           return_type='domain',
                           session=self.session,
                           filters=[Stock1dKdata.factor.is_(None),
                                    Stock1dKdata.timestamp >= to_pd_timestamp('2005-01-01')])
        if kdatas:
            start = kdatas[0].timestamp
            end = kdatas[-1].timestamp

            # get hfq from joinquant
            df = get_price(to_jq_entity_id(entity), start_date=to_time_str(start), end_date=now_time_str(),
                           frequency='daily',
                           fields=['factor', 'open', 'close', 'low', 'high'],
                           skip_paused=True, fq='post')
            if df is not None and not df.empty:
                # fill hfq data
                for kdata in kdatas:
                    if kdata.timestamp in df.index:
                        kdata.hfq_open = df.loc[kdata.timestamp, 'open']
                        kdata.hfq_close = df.loc[kdata.timestamp, 'close']
                        kdata.hfq_high = df.loc[kdata.timestamp, 'high']
                        kdata.hfq_low = df.loc[kdata.timestamp, 'low']
                        kdata.factor = df.loc[kdata.timestamp, 'factor']
                self.session.commit()

                latest_factor = df.factor[-1]
                # factor not change yet, no need to reset the qfq past
                if latest_factor == self.current_factors.get(entity.id):
                    sql = 'UPDATE stock_1d_kdata SET qfq_close=hfq_close/{},qfq_high=hfq_high/{}, qfq_open= hfq_open/{}, qfq_low= hfq_low/{} where ' \
                          'entity_id=\'{}\' and level=\'{}\' and (qfq_close isnull or qfq_high isnull or qfq_low isnull or qfq_open isnull)'.format(
                        latest_factor, latest_factor, latest_factor, latest_factor, entity.id, self.level.value)
                else:
                    sql = 'UPDATE stock_1d_kdata SET qfq_close=hfq_close/{},qfq_high=hfq_high/{}, qfq_open= hfq_open/{}, qfq_low= hfq_low/{} where ' \
                          'entity_id=\'{}\' and level=\'{}\''.format(latest_factor,
                                                                     latest_factor,
                                                                     latest_factor,
                                                                     latest_factor,
                                                                     entity.id,
                                                                     self.level.value)
                self.logger.info(sql)
                self.session.execute(sql)
                self.session.commit()

    def on_finish(self):
        super().on_finish()
        logout()

    def record(self, entity, start, end, size, timestamps):

        start = to_time_str(start, fmt=TIME_FORMAT_DAY1)
        end = now_time_str(fmt=TIME_FORMAT_DAY1)

        if entity.exchange == 'sh':
            exchange_flag = 0
        else:
            exchange_flag = 1

        url = self.url.format(exchange_flag, entity.code, start, end)
        response = requests.get(url=url)

        df = utils.read_csv(io.BytesIO(response.content), encoding='GB2312', na_values='None')

        if df is None:
            return []

        df['name'] = entity.name
        # 指数数据
        if entity.entity_type == 'index':
            df = df.loc[:,
                 ['日期', 'name', '最低价', '开盘价', '收盘价', '最高价', '成交量', '成交金额', '涨跌幅']]
            df.columns = ['timestamp', 'name', 'low', 'open', 'close', 'high', 'volume', 'turnover', 'change_pct']
        # 股票数据
        else:
            df = df.loc[:,
                 ['日期', 'name', '最低价', '开盘价', '收盘价', '最高价', '成交量', '成交金额', '涨跌幅', '换手率']]
            df.columns = ['timestamp', 'name', 'low', 'open', 'close', 'high', 'volume', 'turnover', 'change_pct',
                          'turnover_rate']
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df['provider'] = 'netease'
        df['level'] = self.level.value

        return df.to_dict(orient='records')


if __name__ == '__main__':
    # init_process_log('china_stock_day_kdata.log')
    ChinaStockDayKdataRecorder(level=IntervalLevel.LEVEL_1DAY, codes=['002572']).run()
