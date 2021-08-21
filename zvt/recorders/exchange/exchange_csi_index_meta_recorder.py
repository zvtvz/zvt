# -*- coding: utf-8 -*-

import io

import pandas as pd
import requests

from zvt.api.utils import china_stock_code_to_id
from zvt.contract.api import df_to_db
from zvt.contract.recorder import Recorder
from zvt.domain import Index, IndexCategory
from zvt.recorders.consts import DEFAULT_HEADER
from zvt.utils.time_utils import to_pd_timestamp, now_pd_timestamp


def get_resp_data(resp: requests.Response):
    resp.raise_for_status()
    return resp.json()['list']


# 上证指数 中证指数
class ExchangeIndexMetaRecorder(Recorder):
    original_page_url = 'http://www.csindex.com.cn/zh-CN/indices/index?class_2=2&class_17=17&class_10=10&class_7=7&is_custom_0=1'

    data_schema = Index
    provider = 'exchange'

    url = 'http://www.csindex.com.cn/zh-CN/indices/index?page=1&page_size=1000&by=asc&order=%E5%8F%91%E5%B8%83%E6%97%B6%E9%97%B4&data_type=json' \
          '&{}&class_7=7&class_10=10&{}&is_custom_0=1'

    # 中证指数 抓取 风格指数 行业指数 规模指数
    csi_category_map_url = {
        IndexCategory.style: url.format('class_1=1', 'class_19=19'),
        IndexCategory.industry: url.format('class_1=1', 'class_18=18'),
        IndexCategory.scope: url.format('class_1=1', 'class_17=17'),
    }

    # 上证指数 只取规模指数
    sh_category_map_url = {
        IndexCategory.scope: url.format('class_2=2', 'class_17=17')
    }

    def run(self):
        self.record_index('sh')

    def record_index(self, index_type):
        if index_type == 'csi':
            category_map_url = self.csi_category_map_url
        elif index_type == 'sh':
            category_map_url = self.sh_category_map_url
        else:
            assert False

        requests_session = requests.Session()

        for category, url in category_map_url.items():
            resp = requests_session.get(url, headers=DEFAULT_HEADER)

            results = get_resp_data(resp)
            the_list = []

            self.logger.info(f'category: {category} ')
            self.logger.info(f'results: {results} ')
            for i, result in enumerate(results):
                self.logger.info(f'to {i}/{len(results)}')
                code = result['index_code']
                name = result['indx_sname']
                entity_id = f'index_sh_{code}'
                index_item = {
                    'id': entity_id,
                    'entity_id': entity_id,
                    'timestamp': to_pd_timestamp(result['base_date']),
                    'entity_type': 'index',
                    'exchange': 'sh',
                    'code': code,
                    'name': name,
                    'category': category.value,
                    'list_date': result['online_date'],
                    'base_point': result['base_point'],
                    'publisher': 'csindex'
                }
                self.logger.info(index_item)
                the_list.append(index_item)
            if the_list:
                df = pd.DataFrame.from_records(the_list)
                df_to_db(data_schema=self.data_schema, df=df, provider=self.provider,
                         force_update=True)
            self.logger.info(f"finish record {index_type} index:{category.value}")

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


__all__ = ['ExchangeIndexMetaRecorder']

if __name__ == '__main__':
    spider = ExchangeIndexMetaRecorder()
    spider.run()
# the __all__ is generated
__all__ = ['ExchangeIndexMetaRecorder']
