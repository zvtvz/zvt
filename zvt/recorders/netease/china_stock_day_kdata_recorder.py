# -*- coding: utf-8 -*-
import io

import pandas as pd
import requests
from jqdatasdk import auth, get_price, logout

from zvt.api.common import generate_kdata_id, to_jq_security_id
from zvt.api.technical import get_kdata
from zvt.domain import TradingLevel, SecurityType, Provider, Stock1DKdata, StoreCategory, Stock
from zvt.recorders.recorder import TimeSeriesFetchingStyle, FixedCycleDataRecorder, ApiWrapper
from zvt.settings import JQ_ACCOUNT, JQ_PASSWD
from zvt.utils import utils
from zvt.utils.time_utils import to_time_str, TIME_FORMAT_DAY1, now_time_str, to_pd_timestamp
from zvt.utils.utils import init_process_log


class MyApiWrapper(ApiWrapper):
    def request(self, url=None, method='get', param=None, path_fields=None):
        security_item = param['security_item']

        if security_item.exchange == 'sh':
            exchange_flag = 0
        else:
            exchange_flag = 1

        url = url.format(exchange_flag, security_item.code, param['start'], param['end'])
        response = requests.get(url=url)

        df = utils.read_csv(io.BytesIO(response.content), encoding='GB2312', na_values='None')

        if df is None:
            []

        df['name'] = security_item.name
        # 指数数据
        if security_item.type == 'index':
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
        df['provider'] = Provider.NETEASE.value
        df['level'] = param['level']
        return df.to_dict(orient='records')


class ChinaStockDayKdataRecorder(FixedCycleDataRecorder):
    meta_provider = Provider.EASTMONEY
    meta_schema = Stock

    provider = Provider.NETEASE
    store_category = StoreCategory.stock_1d_kdata
    data_schema = Stock1DKdata
    url = 'http://quotes.money.163.com/service/chddata.html?code={}{}&start={}&end={}&fields=TCLOSE;HIGH;LOW;TOPEN;LCLOSE;CHG;PCHG;TURNOVER;VOTURNOVER;VATURNOVER'
    api_wrapper = MyApiWrapper()

    def __init__(self, security_type=SecurityType.stock, exchanges=['sh', 'sz'], codes=None, batch_size=10,
                 force_update=False, sleeping_time=5, fetching_style=TimeSeriesFetchingStyle.end_size,
                 default_size=2000, contain_unfinished_data=False, level=TradingLevel.LEVEL_1DAY,
                 one_shot=True) -> None:
        super().__init__(security_type, exchanges, codes, batch_size, force_update, sleeping_time, fetching_style,
                         default_size, contain_unfinished_data, level, one_shot)

        self.current_factors = {}
        for security_item in self.securities:
            kdata = get_kdata(security_id=security_item.id, provider=self.provider,
                              level=self.level.value, order=Stock1DKdata.timestamp.desc(),
                              limit=1,
                              return_type='domain',
                              session=self.session)
            if kdata:
                self.current_factors[security_item.id] = kdata[0].factor
                self.logger.info('{} latest factor:{}'.format(security_item.id, kdata[0].factor))

        auth(JQ_ACCOUNT, JQ_PASSWD)

    def get_data_map(self):
        return {}

    def generate_domain_id(self, security_item, original_data):
        return generate_kdata_id(security_id=security_item.id, timestamp=original_data['timestamp'], level=self.level)

    def generate_request_param(self, security_item, start, end, size, timestamp):
        return {
            'security_item': security_item,
            'start': to_time_str(start, fmt=TIME_FORMAT_DAY1),
            'end': now_time_str(fmt=TIME_FORMAT_DAY1),
            'level': self.level.value
        }

    def on_finish(self, security_item):
        kdatas = get_kdata(security_id=security_item.id, level=self.level.value, order=Stock1DKdata.timestamp.asc(),
                           return_type='domain',
                           session=self.session,
                           filters=[Stock1DKdata.factor.is_(None),
                                    Stock1DKdata.timestamp >= to_pd_timestamp('2005-01-01')])
        if kdatas:
            start = kdatas[0].timestamp
            end = kdatas[-1].timestamp

            # get hfq from joinquant
            df = get_price(to_jq_security_id(security_item), start_date=to_time_str(start), end_date=now_time_str(),
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
                if latest_factor == self.current_factors.get(security_item.id):
                    sql = 'UPDATE stock_1d_kdata SET qfq_close=hfq_close/{},qfq_high=hfq_high/{}, qfq_open= hfq_open/{}, qfq_low= hfq_low/{} where ' \
                          'security_id=\'{}\' and level=\'{}\' and (qfq_close isnull or qfq_high isnull or qfq_low isnull or qfq_open isnull)'.format(
                        latest_factor, latest_factor, latest_factor, latest_factor, security_item.id, self.level.value)
                else:
                    sql = 'UPDATE stock_1d_kdata SET qfq_close=hfq_close/{},qfq_high=hfq_high/{}, qfq_open= hfq_open/{}, qfq_low= hfq_low/{} where ' \
                          'security_id=\'{}\' and level=\'{}\''.format(latest_factor,
                                                                       latest_factor,
                                                                       latest_factor,
                                                                       latest_factor,
                                                                       security_item.id,
                                                                       self.level.value)
                self.logger.info(sql)
                self.session.execute(sql)
                self.session.commit()

    def on_stop(self):
        super().on_stop()
        logout()


if __name__ == '__main__':
    init_process_log('china_stock_day_kdata.log')
    ChinaStockDayKdataRecorder(level=TradingLevel.LEVEL_1DAY, codes=['000338']).run()
