# -*- coding: utf-8 -*-

import time

import requests
import pandas as pd

from zvt.domain import Index, Index1DKdata
from zvt.api.common import generate_kdata_id
from zvt.recorders.recorder import ApiWrapper, FixedCycleDataRecorder, Provider, SecurityType
from zvt.utils.time_utils import get_year_quarters, is_same_date


class SinaIndexKdataApiWrapper(ApiWrapper):
    def request(self, url=None, method='get', param=None, path_fields=None):
        security_item = param['security_item']
        quarters = param['quarters']
        level = param['level']

        result_df = pd.DataFrame()
        for year, quarter in quarters:
            query_url = url.format(security_item.code, year, quarter)
            response = requests.get(query_url)
            response.encoding = 'gbk'

            try:
                dfs = pd.read_html(response.text)
            except ValueError as error:
                self.logger.error(f'skip ({year}-{quarter:02d}){security_item.code}{security_item.name}({error})')
                time.sleep(10.0)
                continue

            if len(dfs) < 5:
                time.sleep(10.0)
                continue

            df = dfs[4].copy()
            df = df.iloc[1:]
            df.columns = ['timestamp', 'open', 'high', 'close', 'low', 'volume', 'turnover']
            df['name'] = security_item.name
            df['level'] = level
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df['provider'] = Provider.SINA.value

            result_df = pd.concat([result_df, df])

            self.logger.info(f'({security_item.code}{security_item.name})({year}-{quarter:02d})')
            time.sleep(10.0)

        result_df = result_df.sort_values(by='timestamp')

        return result_df.to_dict(orient='records')


class ChinaIndexDayKdataRecorder(FixedCycleDataRecorder):
    meta_provider = Provider.EXCHANGE
    meta_schema = Index

    provider = Provider.SINA
    data_schema = Index1DKdata
    api_wrapper = SinaIndexKdataApiWrapper()
    url = 'http://vip.stock.finance.sina.com.cn/corp/go.php/vMS_MarketHistory/stockid/{}/type/S.phtml?year={}&jidu={}'
    
    def __init__(self, security_type=SecurityType.index, exchanges=['cn']):
        super(ChinaIndexDayKdataRecorder, self).__init__(security_type, exchanges)

    def get_data_map(self):
        return {}

    def generate_domain_id(self, security_item, original_data):
        return generate_kdata_id(security_item.id, timestamp=original_data['timestamp'], level=self.level)

    def generate_request_param(self, security_item, start, end, size, timestamp):
        the_quarters = get_year_quarters(start)
        if not is_same_date(security_item.timestamp, start) and len(the_quarters) > 1:
            the_quarters = the_quarters[1:]

        return {
            'security_item': security_item,
            'quarters': the_quarters,
            'level': self.level.value
        }


if __name__ == '__main__':
    ChinaIndexDayKdataRecorder().run()
