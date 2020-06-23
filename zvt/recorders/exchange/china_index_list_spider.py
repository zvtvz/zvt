# -*- coding: utf-8 -*-

import io

import demjson
import pandas as pd
import requests

from zvt.contract.api import df_to_db
from zvt.contract.recorder import Recorder
from zvt.utils.time_utils import to_pd_timestamp, now_pd_timestamp
from zvt.api.quote import china_stock_code_to_id
from zvt.domain import IndexStock, Index


class ChinaIndexListSpider(Recorder):
    data_schema = IndexStock

    def __init__(self, batch_size=10, force_update=False, sleeping_time=2.0, provider='exchange') -> None:
        self.provider = provider
        super().__init__(batch_size, force_update, sleeping_time)

    def run(self):
        # 上证、中证
        self.fetch_csi_index()

        # 深证
        self.fetch_szse_index()

        # 国证
        # FIXME:已不可用
        # self.fetch_cni_index()

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

            index_list.extend(response_index_list)

            self.logger.info(f'上证、中证指数第 {page} 页抓取完成...')
            page += 1
            self.sleep()

        df = pd.DataFrame(index_list)
        df = df[['base_date', 'base_point', 'index_code', 'indx_sname', 'online_date', 'class_eseries']].copy()
        df.columns = ['timestamp', 'base_point', 'code', 'name', 'list_date', 'class_eseries']
        df['category'] = df['class_eseries'].apply(lambda x: x.split(' ')[0].lower())
        df = df.drop('class_eseries', axis=1)
        df = df.loc[df['code'].str.contains(r'^\d{6}$')]

        self.persist_index(df)
        self.logger.info('上证、中证指数列表抓取完成...')

        # 抓取上证、中证指数成分股
        self.fetch_csi_index_component(df)
        self.logger.info('上证、中证指数成分股抓取完成...')

    def fetch_csi_index_component(self, df: pd.DataFrame):
        """
        抓取上证、中证指数成分股
        """
        query_url = 'http://www.csindex.com.cn/uploads/file/autofile/cons/{}cons.xls'

        for _, index in df.iterrows():
            index_code = index['code']

            url = query_url.format(index_code)

            try:
                response = requests.get(url)
                response.raise_for_status()
            except requests.HTTPError as error:
                self.logger.error(f'{index["name"]} - {index_code} 成分股抓取错误 ({error})')
                continue

            response_df = pd.read_excel(io.BytesIO(response.content))

            response_df = response_df[['成分券代码Constituent Code', '成分券名称Constituent Name']].rename(
                columns={'成分券代码Constituent Code': 'stock_code',
                         '成分券名称Constituent Name': 'stock_name'})

            index_id = f'index_cn_{index_code}'
            response_df['entity_id'] = index_id
            response_df['entity_type'] = 'index'
            response_df['exchange'] = 'cn'
            response_df['code'] = index_code
            response_df['name'] = index['name']
            response_df['timestamp'] = now_pd_timestamp()

            response_df['stock_id'] = response_df['stock_code'].apply(lambda x: china_stock_code_to_id(str(x)))
            response_df['id'] = response_df['stock_id'].apply(
                lambda x: f'{index_id}_{x}')

            df_to_db(data_schema=self.data_schema, df=response_df, provider=self.provider, force_update=True)
            self.logger.info(f'{index["name"]} - {index_code} 成分股抓取完成...')

            self.sleep()

    def fetch_szse_index(self) -> None:
        """
        抓取深证指数列表
        """
        url = 'http://www.szse.cn/api/report/ShowReport?SHOWTYPE=xlsx&CATALOGID=1812_zs&TABKEY=tab1'
        response = requests.get(url)
        df = pd.read_excel(io.BytesIO(response.content), dtype='str')

        df.columns = ['code', 'name', 'timestamp', 'base_point', 'list_date']
        df['category'] = 'szse'
        df = df.loc[df['code'].str.contains(r'^\d{6}$')]
        self.persist_index(df)
        self.logger.info('深证指数列表抓取完成...')

        # 抓取深证指数成分股
        self.fetch_szse_index_component(df)
        self.logger.info('深证指数成分股抓取完成...')

    def fetch_szse_index_component(self, df: pd.DataFrame):
        """
        抓取深证指数成分股
        """
        query_url = 'http://www.szse.cn/api/report/ShowReport?SHOWTYPE=xlsx&CATALOGID=1747_zs&TABKEY=tab1&ZSDM={}'

        for _, index in df.iterrows():
            index_code = index['code']

            url = query_url.format(index_code)
            response = requests.get(url)

            response_df = pd.read_excel(io.BytesIO(response.content), dtype='str')

            index_id = f'index_cn_{index_code}'
            response_df['entity_id'] = index_id
            response_df['entity_type'] = 'index'
            response_df['exchange'] = 'cn'
            response_df['code'] = index_code
            response_df['name'] = index['name']
            response_df['timestamp'] = now_pd_timestamp()

            response_df.rename(columns={'证券代码': 'stock_code', '证券简称': 'stock_name'}, inplace=True)
            response_df['stock_id'] = response_df['stock_code'].apply(lambda x: china_stock_code_to_id(str(x)))

            response_df['id'] = response_df['stock_id'].apply(
                lambda x: f'{index_id}_{x}')

            df_to_db(data_schema=self.data_schema, df=response_df, provider=self.provider)
            self.logger.info(f'{index["name"]} - {index_code} 成分股抓取完成...')

            self.sleep()

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
            df.astype('str')

            result_df = pd.concat([result_df, df])

        result_df = result_df.drop('样本股数量', axis=1)
        result_df.columns = ['name', 'code', 'timestamp', 'base_point', 'list_date']
        result_df['timestamp'] = result_df['timestamp'].apply(lambda x: x.replace('-', ''))
        result_df['list_date'] = result_df['list_date'].apply(lambda x: x.replace('-', ''))
        result_df['category'] = 'csi'
        result_df = result_df.loc[result_df['code'].str.contains(r'^\d{6}$')]

        self.persist_index(result_df)
        self.logger.info('国证指数列表抓取完成...')

        # 抓取国证指数成分股
        self.fetch_cni_index_component(result_df)
        self.logger.info('国证指数成分股抓取完成...')

    def fetch_cni_index_component(self, df: pd.DataFrame):
        """
        抓取国证指数成分股
        """
        query_url = 'http://www.cnindex.com.cn/docs/yb_{}.xls'

        for _, index in df.iterrows():
            index_code = index['code']

            url = query_url.format(index_code)

            try:
                response = requests.get(url)
                response.raise_for_status()
            except requests.HTTPError as error:
                self.logger.error(f'{index["name"]} - {index_code} 成分股抓取错误 ({error})')
                continue

            response_df = pd.read_excel(io.BytesIO(response.content), dtype='str')

            index_id = f'index_cn_{index_code}'

            try:
                response_df = response_df[['样本股代码']]
            except KeyError:
                response_df = response_df[['证券代码']]

            response_df['entity_id'] = index_id
            response_df['entity_type'] = 'index'
            response_df['exchange'] = 'cn'
            response_df['code'] = index_code
            response_df['name'] = index['name']
            response_df['timestamp'] = now_pd_timestamp()

            response_df.columns = ['stock_code']
            response_df['stock_id'] = response_df['stock_code'].apply(lambda x: china_stock_code_to_id(str(x)))
            response_df['id'] = response_df['stock_id'].apply(
                lambda x: f'{index_id}_{x}')

            df_to_db(data_schema=self.data_schema, df=response_df, provider=self.provider)
            self.logger.info(f'{index["name"]} - {index_code} 成分股抓取完成...')

            self.sleep()

    def persist_index(self, df) -> None:
        df['timestamp'] = df['timestamp'].apply(lambda x: to_pd_timestamp(x))
        df['list_date'] = df['list_date'].apply(lambda x: to_pd_timestamp(x))
        df['id'] = df['code'].apply(lambda code: f'index_cn_{code}')
        df['entity_id'] = df['id']
        df['exchange'] = 'cn'
        df['entity_type'] = 'index'

        df = df.dropna(axis=0, how='any')
        df = df.drop_duplicates(subset='id', keep='last')

        df_to_db(df=df, data_schema=Index, provider=self.provider, force_update=False)


__all__ = ['ChinaIndexListSpider']

if __name__ == '__main__':
    spider = ChinaIndexListSpider(provider='exchange')
    spider.run()
