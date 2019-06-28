# -*- coding: utf-8 -*-

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

    def download_etf_list(self, response: requests.Response, exchange: str) -> None:
        df = None
        if exchange == 'sh':
            response_dict = demjson.decode(response.text)
            df = pd.DataFrame(response_dict['result'])

            if df is not None:
                df = df[['FUND_ID', 'FUND_NAME']]

        elif exchange == 'sz':
            pass

        if df is not None:
            df.columns = ['code', 'name']

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
