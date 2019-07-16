# -*- coding: utf-8 -*-

import io

import demjson
import requests
import pandas as pd

from zvt.api.technical import init_securities
from zvt.domain import Provider, StockIndex
from zvt.recorders.recorder import Recorder


class ChinaIndexListSpider(Recorder):
    data_schema = StockIndex

    def __init__(self, batch_size=10, force_update=False, sleeping_time=2.0, provider=Provider.EXCHANGE) -> None:
        self.provider = provider
        super(ChinaIndexListSpider, self).__init__(batch_size, force_update, sleeping_time)

    def run(self):
        # 上证、中证
        self.fetch_csi_index()

        # 深证
        self.fetch_szse_index()

        # 国证
        self.fetch_cni_index()

    def fetch_csi_index(self) -> None:
        """
        抓取上证、中证指数列表
        """
        url = 'http://www.csindex.com.cn/zh-CN/indices/index' \
            '?page={}&page_size={}&data_type=json&class_1=1&class_2=2&class_7=7&class_10=10'

        index_list = []
        page = 1
        page_size = 50
        while True:
            query_url = url.format(page, page_size)
            response = requests.get(query_url)
            response_dict = demjson.decode(response.text)
            response_index_list = response_dict.get('list', [])

            if len(response_index_list) == 0:
                break

            index_list.extend(response_dict.get('list', []))

            self.logger.info(f'上证、中证指数第 {page} 页抓取完成...')
            page += 1
            self.sleep()

        df = pd.DataFrame(index_list)
        df = df[['base_date', 'base_point', 'index_code', 'indx_sname', 'online_date', 'class_eseries']]
        df.columns = ['timestamp', 'base_point', 'code', 'name', 'online_date', 'class_eseries']
        df['category'] = df['class_eseries'].apply(lambda x: x.split(' ')[0].lower())
        df = df.drop('class_eseries', axis=1)

        self.persist_index(df)
        self.logger.info('上证、中证指数全部抓取完成...')

    def fetch_szse_index(self) -> None:
        """
        抓取深证指数列表
        """
        url = 'http://www.szse.cn/api/report/ShowReport?SHOWTYPE=xlsx&CATALOGID=1812_zs&TABKEY=tab1'
        response = requests.get(url)
        df = pd.read_excel(io.BytesIO(response.content))

        df.columns = ['code', 'name', 'timestamp', 'base_point', 'online_date']
        df['category'] = 'szse'
        self.persist_index(df)
        self.logger.info('深证指数抓取完成...')

    def fetch_cni_index(self) -> None:
        """
        抓取国证指数列表
        """
        url = 'http://www.cnindex.com.cn/zstx/jcxl/'
        response = requests.get(url)
        response.encoding = 'utf-8'
        dfs = pd.read_html(response.text)

        # 第 9 个 table 之后为非股票指数
        dfs = dfs[1:9]

        result_df = pd.DataFrame()
        for df in dfs:
            header = df.iloc[0]
            df = df[1:]
            df.columns = header

            result_df = pd.concat([result_df, df])

        result_df = result_df.drop('样本股数量', axis=1)
        result_df.columns = ['name', 'code', 'timestamp', 'base_point', 'online_date']
        result_df['timestamp'] = result_df['timestamp'].apply(lambda x: x.replace('-', ''))
        result_df['online_date'] = result_df['online_date'].apply(lambda x: x.replace('-', ''))
        result_df['category'] = 'csi'

        self.persist_index(result_df)
        self.logger.info('国证指数抓取完成...')

    def persist_index(self, df) -> None:
        df['id'] = df['code'].apply(lambda code: f'index_cn_{code}')
        df['exchange'] = 'cn'
        df['type'] = 'index'
        df['is_delisted'] = False

        df = df.dropna(axis=0, how='any')
        df = df.drop_duplicates(subset='id', keep='last')

        init_securities(df, security_type='index', provider=self.provider)


if __name__ == '__main__':
    spider = ChinaIndexListSpider(provider=Provider.EXCHANGE)
    spider.run()
