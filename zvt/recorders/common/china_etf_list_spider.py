# -*- coding: utf-8 -*-

import io

import demjson
import requests
import pandas as pd

from zvt.api.technical import init_securities
from zvt.recorders.consts import DEFAULT_SH_ETF_LIST_HEADER
from zvt.domain import Provider, Index
from zvt.recorders.recorder import Recorder


class ChinaETFListSpider(Recorder):
    data_schema = Index

    def __init__(self, batch_size=10, force_update=False, sleeping_time=10, provider=Provider.EXCHANGE) -> None:
        self.provider = provider
        super().__init__(batch_size, force_update, sleeping_time)

    def run(self):
        url = 'http://query.sse.com.cn/commonQuery.do?sqlId=COMMON_SSE_ZQPZ_ETFLB_L_NEW&_=1561697608673'

        resp = requests.get(url, headers=DEFAULT_SH_ETF_LIST_HEADER)
        self.download_etf_list(response=resp, exchange='sh')

        url = 'http://www.szse.cn/api/report/ShowReport?SHOWTYPE=xlsx&CATALOGID=1105&TABKEY=tab1&selectJjlb=ETF'

        resp = requests.get(url)
        self.download_etf_list(response=resp, exchange='sz')

    def download_etf_list(self, response: requests.Response, exchange: str) -> None:
        df = None
        if exchange == 'sh':
            response_dict = demjson.decode(response.text)
            df = pd.DataFrame(response_dict['result'])
            if df is not None:
                df = df[['FUND_ID', 'FUND_NAME']]
                df.columns = ['code', 'name']

        elif exchange == 'sz':
            df = pd.read_excel(io.BytesIO(response.content), dtype=str, parse_dates=['上市日期'])
            if df is not None:
                df = df[['基金代码', '基金简称', '上市日期']]
                df.columns = ['code', 'name', 'timestamp']

        if df is not None:
            df['id'] = df['code'].apply(lambda x: f'index_{exchange}_{x}')
            df['exchange'] = exchange
            df['type'] = 'index'
            df['category'] = 'etf'

            df = df.dropna(axis=0, how='any')
            df = df.drop_duplicates(subset='id', keep='last')

            init_securities(df, security_type='index', provider=self.provider)


if __name__ == '__main__':
    spider = ChinaETFListSpider(provider=Provider.EXCHANGE)
    spider.run()
