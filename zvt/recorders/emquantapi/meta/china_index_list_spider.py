# -*- coding: utf-8 -*-

import io
from EmQuantAPI import *
import demjson
import pandas as pd
import requests
from jqdatasdk import get_query_count, auth, logout, get_all_securities

from zvt import zvt_env
from zvt.contract.api import df_to_db
from zvt.contract.recorder import Recorder
from zvt.recorders.emquantapi.common import mainCallback
from zvt.utils.time_utils import to_pd_timestamp, now_pd_timestamp, to_time_str
from zvt.api.quote import china_stock_code_to_id
from zvt.domain import IndexStock, Index


class ChinaIndexListSpider(Recorder):
    data_schema = Index

    provider = 'emquantapi'

    def __init__(self, batch_size=10, force_update=True, sleeping_time=10) -> None:
        super().__init__(batch_size, force_update, sleeping_time)

    # 调用登录函数（激活后使用，不需要用户名密码）
    # loginResult = c.start("ForceLogin=1", '', mainCallback)
    # if (loginResult.ErrorCode != 0):
    #     print("login in fail")
    #     exit()

    def on_finish(self):
        logout()

    def run(self):
        def is_sh(x):
            if ".SH" in x:
                return x

        def is_sz(x):
            if ".SZ" in x:
                return x

        self.colums_map = {
            'BASICPOINT': 'base_point',  # 基准点数
            'BASICDATE': 'base_date',  # 指数基期
            'MAKERNAME': 'publisher',  # 编制机构
            'DELISTDATE': 'end_date',  # 指数退市日期
            'SHORTNAME': 'name',  # 指数简称
            'PUBLISHDATE': 'list_date'  # 指数发布日期
        }

        self.now_date = to_time_str(now_pd_timestamp())
        # self.index_all=c.sector("905001001",self.now_date)
        # 905002 上证指数
        data1 = c.sector("905002", self.now_date)
        # 905006 深证指数
        data2 = c.sector("905006", self.now_date)
        # 905009 中证指数
        data3 = c.sector("905009", self.now_date)
        # 905001 市场指数
        data4 = c.sector("905001", self.now_date)
        self.index_all = data1.Data + data2.Data + data3.Data + data4.Data
        # 上证、中证
        self.fetch_csi_index(list(filter(is_sh, self.index_all)))

        # 深证z
        self.fetch_szse_index(list(filter(is_sz, self.index_all)))

        # 国证
        # FIXME:已不可用
        # self.fetch_cni_index()

    def fetch_csi_index(self, sh_data) -> None:
        """
        抓取上证、中证指数列表
        """
        df = pd.DataFrame()
        for em_code in set(sh_data):
            if len(em_code)>9:
                continue
            data = c.css(em_code, [i for i in self.colums_map.keys()], "TradeDate=" + self.now_date + ",ispandas=1")
            try:
                data['code'] = em_code[:6]
            except TypeError:
                print(em_code)
                continue
            df = df.append(data)
        df = df.rename(columns=self.colums_map)
        df['timestamp'] = pd.to_datetime(df.list_date)
        df['exchange'] = 'sh'
        df['category'] = 'main'
        df['entity_type'] = 'index'
        df['entity_id'] = df.apply(lambda x: 'index' + '_' + 'sh' + '_' + x.code, axis=1)
        df['id'] = df['entity_id']

        # df['codes'] = df.index
        # df['code_len'] = df.apply(lambda x:len(x.codes),axis=1)
        # df = df.query("code_len==9")
        df_to_db(df=df, data_schema=Index, provider=self.provider, force_update=False)

        self.logger.info('上证、中证指数列表写入完成...')

        # 抓取上证、中证指数成分股
        # self.fetch_csi_index_component(df)
        # self.logger.info('上证、中证指数成分股抓取完成...')

    def fetch_csi_index_component(self, df: pd.DataFrame):
        """
        抓取上证、中证指数成分股
        """

        # df_to_db(data_schema=self.data_schema, df=response_df, provider=self.provider, force_update=True)
        # self.logger.info(f'{index["name"]} - {index_code} 成分股抓取完成...')
        #
        # self.sleep()

    def fetch_szse_index(self, sz_data) -> None:
        """
        抓取深证指数列表
        """
        df = pd.DataFrame()
        for em_code in set(sz_data):
            if len(em_code)>9:
                continue
            data = c.css(em_code, [i for i in self.colums_map.keys()], "TradeDate=" + self.now_date + ",ispandas=1")
            data['code'] = em_code[:6]
            df = df.append(data)
        df = df.rename(columns=self.colums_map)
        df['timestamp'] = pd.to_datetime(df.list_date)
        df['exchange'] = 'sz'
        df['category'] = 'main'
        df['entity_type'] = 'index'
        df['entity_id'] = df.apply(lambda x: 'index' + '_' + 'sz' + '_' + x.code, axis=1)
        df['id'] = df['entity_id']
        df_to_db(df=df, data_schema=Index, provider=self.provider, force_update=False)
        self.logger.info('深证指数列表写入完成...')
        # 抓取深证指数成分股
        # self.fetch_szse_index_component(df)
        # self.logger.info('深证指数成分股抓取完成...')

    def fetch_szse_index_component(self, df: pd.DataFrame):
        """
        抓取深证指数成分股
        """

        # df_to_db(data_schema=self.data_schema, df=response_df, provider=self.provider)
        # self.logger.info(f'{index["name"]} - {index_code} 成分股抓取完成...')
        #
        # self.sleep()

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
