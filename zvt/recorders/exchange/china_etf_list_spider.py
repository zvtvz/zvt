# -*- coding: utf-8 -*-

import io
import re

import demjson
import pandas as pd
import requests

from zvt.contract.api import df_to_db
from zvt.contract.recorder import Recorder
from zvt.utils.time_utils import now_pd_timestamp
from zvt.api.quote import china_stock_code_to_id
from zvt.domain import EtfStock, BlockCategory, Etf
from zvt.recorders.consts import DEFAULT_SH_ETF_LIST_HEADER


class ChinaETFListSpider(Recorder):
    data_schema = EtfStock

    def __init__(self, batch_size=10, force_update=False, sleeping_time=10.0, provider='exchange') -> None:
        self.provider = provider
        super().__init__(batch_size, force_update, sleeping_time)

    def run(self):
        # 抓取沪市 ETF 列表
        url = 'http://query.sse.com.cn/commonQuery.do?sqlId=COMMON_SSE_ZQPZ_ETFLB_L_NEW'
        response = requests.get(url, headers=DEFAULT_SH_ETF_LIST_HEADER)
        response_dict = demjson.decode(response.text)

        df = pd.DataFrame(response_dict.get('result', []))
        self.persist_etf_list(df, exchange='sh')
        self.logger.info('沪市 ETF 列表抓取完成...')

        # 抓取沪市 ETF 成分股
        self.download_sh_etf_component(df)
        self.logger.info('沪市 ETF 成分股抓取完成...')

        # 抓取深市 ETF 列表
        url = 'http://www.szse.cn/api/report/ShowReport?SHOWTYPE=xlsx&CATALOGID=1945'
        response = requests.get(url)

        df = pd.read_excel(io.BytesIO(response.content), dtype=str)
        self.persist_etf_list(df, exchange='sz')
        self.logger.info('深市 ETF 列表抓取完成...')

        # 抓取深市 ETF 成分股
        self.download_sz_etf_component(df)
        self.logger.info('深市 ETF 成分股抓取完成...')

    def persist_etf_list(self, df: pd.DataFrame, exchange: str):
        if df is None:
            return

        df = df.copy()
        if exchange == 'sh':
            df = df[['FUND_ID', 'FUND_NAME']]
        elif exchange == 'sz':
            df = df[['证券代码', '证券简称']]

        df.columns = ['code', 'name']
        df['id'] = df['code'].apply(lambda code: f'etf_{exchange}_{code}')
        df['entity_id'] = df['id']
        df['exchange'] = exchange
        df['entity_type'] = 'etf'
        df['category'] = BlockCategory.etf.value

        df = df.dropna(axis=0, how='any')
        df = df.drop_duplicates(subset='id', keep='last')

        df_to_db(df=df, data_schema=Etf, provider=self.provider, force_update=False)

    def download_sh_etf_component(self, df: pd.DataFrame):
        """
        ETF_CLASS => 1. 单市场 ETF 2.跨市场 ETF 3. 跨境 ETF
                        5. 债券 ETF 6. 黄金 ETF
        :param df: ETF 列表数据
        :return: None
        """
        query_url = 'http://query.sse.com.cn/infodisplay/queryConstituentStockInfo.do?' \
                    'isPagination=false&type={}&etfClass={}'

        etf_df = df[(df['ETF_CLASS'] == '1') | (df['ETF_CLASS'] == '2')]
        etf_df = self.populate_sh_etf_type(etf_df)

        for _, etf in etf_df.iterrows():
            url = query_url.format(etf['ETF_TYPE'], etf['ETF_CLASS'])
            response = requests.get(url, headers=DEFAULT_SH_ETF_LIST_HEADER)
            response_dict = demjson.decode(response.text)
            response_df = pd.DataFrame(response_dict.get('result', []))

            etf_code = etf['FUND_ID']
            etf_id = f'etf_sh_{etf_code}'
            response_df = response_df[['instrumentId', 'instrumentName']].copy()
            response_df.rename(columns={'instrumentId': 'stock_code', 'instrumentName': 'stock_name'}, inplace=True)

            response_df['entity_id'] = etf_id
            response_df['entity_type'] = 'etf'
            response_df['exchange'] = 'sh'
            response_df['code'] = etf_code
            response_df['name'] = etf['FUND_NAME']
            response_df['timestamp'] = now_pd_timestamp()

            response_df['stock_id'] = response_df['stock_code'].apply(lambda code: china_stock_code_to_id(code))
            response_df['id'] = response_df['stock_id'].apply(
                lambda x: f'{etf_id}_{x}')

            df_to_db(data_schema=self.data_schema, df=response_df, provider=self.provider)
            self.logger.info(f'{etf["FUND_NAME"]} - {etf_code} 成分股抓取完成...')

            self.sleep()

    def download_sz_etf_component(self, df: pd.DataFrame):
        query_url = 'http://vip.stock.finance.sina.com.cn/corp/go.php/vII_NewestComponent/indexid/{}.phtml'

        self.parse_sz_etf_underlying_index(df)
        for _, etf in df.iterrows():
            underlying_index = etf['拟合指数']
            etf_code = etf['证券代码']

            if len(underlying_index) == 0:
                self.logger.info(f'{etf["证券简称"]} - {etf_code} 非 A 股市场指数，跳过...')
                continue

            url = query_url.format(underlying_index)
            response = requests.get(url)
            response.encoding = 'gbk'

            try:
                dfs = pd.read_html(response.text, header=1)
            except ValueError as error:
                self.logger.error(f'HTML parse error: {error}, response: {response.text}')
                continue

            if len(dfs) < 4:
                continue

            response_df = dfs[3].copy()
            response_df = response_df.dropna(axis=1, how='any')
            response_df['品种代码'] = response_df['品种代码'].apply(lambda x: f'{x:06d}')

            etf_id = f'etf_sz_{etf_code}'
            response_df = response_df[['品种代码', '品种名称']].copy()
            response_df.rename(columns={'品种代码': 'stock_code', '品种名称': 'stock_name'}, inplace=True)

            response_df['entity_id'] = etf_id
            response_df['entity_type'] = 'etf'
            response_df['exchange'] = 'sz'
            response_df['code'] = etf_code
            response_df['name'] = etf['证券简称']
            response_df['timestamp'] = now_pd_timestamp()

            response_df['stock_id'] = response_df['stock_code'].apply(lambda code: china_stock_code_to_id(code))
            response_df['id'] = response_df['stock_id'].apply(
                lambda x: f'{etf_id}_{x}')

            df_to_db(data_schema=self.data_schema, df=response_df, provider=self.provider)
            self.logger.info(f'{etf["证券简称"]} - {etf_code} 成分股抓取完成...')

            self.sleep()

    @staticmethod
    def populate_sh_etf_type(df: pd.DataFrame):
        """
        填充沪市 ETF 代码对应的 TYPE 到列表数据中
        :param df: ETF 列表数据
        :return: 包含 ETF 对应 TYPE 的列表数据
        """
        query_url = 'http://query.sse.com.cn/infodisplay/queryETFNewAllInfo.do?' \
                    'isPagination=false&type={}&pageHelp.pageSize=25'

        type_df = pd.DataFrame()
        for etf_class in [1, 2]:
            url = query_url.format(etf_class)
            response = requests.get(url, headers=DEFAULT_SH_ETF_LIST_HEADER)
            response_dict = demjson.decode(response.text)
            response_df = pd.DataFrame(response_dict.get('result', []))
            response_df = response_df[['fundid1', 'etftype']]

            type_df = pd.concat([type_df, response_df])

        result_df = df.copy()
        result_df = result_df.sort_values(by='FUND_ID').reset_index(drop=True)
        type_df = type_df.sort_values(by='fundid1').reset_index(drop=True)

        result_df['ETF_TYPE'] = type_df['etftype']

        return result_df

    @staticmethod
    def parse_sz_etf_underlying_index(df: pd.DataFrame):
        """
        解析深市 ETF 对应跟踪的指数代码
        :param df: ETF 列表数据
        :return: 解析完成 ETF 对应指数代码的列表数据
        """

        def parse_index(text):
            if len(text) == 0:
                return ''

            result = re.search(r"(\d+).*", text)
            if result is None:
                return ''
            else:
                return result.group(1)

        df['拟合指数'] = df['拟合指数'].apply(parse_index)


__all__ = ['ChinaETFListSpider']

if __name__ == '__main__':
    spider = ChinaETFListSpider(provider='exchange')
    spider.run()
