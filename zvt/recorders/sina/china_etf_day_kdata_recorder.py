# -*- coding: utf-8 -*-

import demjson
import logging
import pandas as pd
import requests

from zvt.api.common import generate_kdata_id
from zvt.recorders.consts import EASTMONEY_ETF_NET_VALUE_HEADER
from zvt.api.technical import get_kdata
from zvt.domain import Index, Provider, SecurityType, StoreCategory, TradingLevel, Index1DKdata
from zvt.recorders.recorder import ApiWrapper, FixedCycleDataRecorder, TimeSeriesFetchingStyle
from zvt.utils.time_utils import to_time_str
from zvt.utils.utils import init_process_log

logger = logging.getLogger(__name__)


class MyApiWrapper(ApiWrapper):
    def request(self, url=None, method='post', param=None, path_fields=None):
        security_item = param['security_item']
        size = param['size']

        url = url.format(security_item.exchange, security_item.code, size)

        response = requests.get(url)
        response_json = demjson.decode(response.text)

        if response_json is None or len(response_json) == 0:
            return []

        df = pd.DataFrame(response_json)
        df.rename(columns={'day': 'timestamp'}, inplace=True)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df['name'] = security_item.name
        df['provider'] = Provider.SINA.value
        df['level'] = param['level']

        return df.to_dict(orient='records')


class ChinaETFDayKdataRecorder(FixedCycleDataRecorder):
    meta_provider = Provider.EXCHANGE
    meta_schema = Index

    provider = Provider.SINA
    data_schema = Index1DKdata
    url = 'http://money.finance.sina.com.cn/quotes_service/api/json_v2.php/CN_MarketData.getKLineData?' \
          'symbol={}{}&scale=240&&datalen={}&ma=no'
    api_wrapper = MyApiWrapper()

    def __init__(self, security_type=SecurityType.index, exchanges=['sh', 'sz'], codes=None, batch_size=10,
                 force_update=False, sleeping_time=5, fetching_style=TimeSeriesFetchingStyle.end_size,
                 default_size=2000, contain_unfinished_data=False, level=TradingLevel.LEVEL_1DAY,
                 one_shot=True) -> None:
        super().__init__(security_type, exchanges, codes, batch_size, force_update, sleeping_time, fetching_style,
                         default_size, contain_unfinished_data, level, one_shot)

    def get_data_map(self):
        return {}

    def generate_domain_id(self, security_item, original_data):
        return generate_kdata_id(security_id=security_item.id, timestamp=original_data['timestamp'], level=self.level)

    def generate_request_param(self, security_item, start, end, size, timestamp):
        # 此 url 不支持分页，如果超过我们想取的条数，则只能取最大条数
        if start is None or size > self.default_size:
            size = 8000

        return {
            'security_item': security_item,
            'level': self.level.value,
            'size': size
        }

    def on_finish(self, security_item):
        kdatas = get_kdata(security_id=security_item.id, level=TradingLevel.LEVEL_1DAY.value,
                           order=Index1DKdata.timestamp.asc(),
                           return_type='domain', session=self.session,
                           filters=[Index1DKdata.cumulative_net_value.is_(None)])

        if kdatas and len(kdatas) > 0:
            start = kdatas[0].timestamp
            end = kdatas[-1].timestamp

            # 从东方财富获取基金累计净值
            df = self.fetch_cumulative_net_value(security_item, start, end)

            if df is not None and not df.empty:
                for kdata in kdatas:
                    if kdata.timestamp in df.index:
                        kdata.cumulative_net_value = df.loc[kdata.timestamp, 'LJJZ']
                        kdata.change_pct = df.loc[kdata.timestamp, 'JZZZL']
                self.session.commit()
                self.logger.info(f'{security_item.code} - {security_item.name}累计净值更新完成...')

    def fetch_cumulative_net_value(self, security_item, start, end) -> pd.DataFrame:
        query_url = 'http://api.fund.eastmoney.com/f10/lsjz?' \
                    'fundCode={}&pageIndex={}&pageSize=200&startDate={}&endDate={}'

        page = 1
        df = pd.DataFrame()
        while True:
            url = query_url.format(security_item.code, page, to_time_str(start), to_time_str(end))

            response = requests.get(url, headers=EASTMONEY_ETF_NET_VALUE_HEADER)
            response_json = demjson.decode(response.text)
            response_df = pd.DataFrame(response_json['Data']['LSJZList'])

            # 最后一页
            if response_df.empty:
                break

            response_df['FSRQ'] = pd.to_datetime(response_df['FSRQ'])
            response_df['JZZZL'] = pd.to_numeric(response_df['JZZZL'], errors='coerce')
            response_df['LJJZ'] = pd.to_numeric(response_df['LJJZ'], errors='coerce')
            response_df = response_df.fillna(0)
            response_df.set_index('FSRQ', inplace=True, drop=True)

            df = pd.concat([df, response_df])
            page += 1

            self.sleep()

        return df


if __name__ == '__main__':
    init_process_log('sina_china_etf_day_kdata.log')
    ChinaETFDayKdataRecorder(level=TradingLevel.LEVEL_1DAY).run()

