# -*- coding: utf-8 -*-

import io

import pandas as pd
import requests

from zvt.api.utils import china_stock_code_to_id
from zvt.contract.api import df_to_db
from zvt.contract.recorder import Recorder, TimeSeriesDataRecorder
from zvt.domain import Index, IndexCategory, IndexStock
from zvt.recorders.consts import DEFAULT_HEADER
from zvt.utils.time_utils import to_pd_timestamp


# 上证指数 中证指数
class ExchangeCSIndexMetaRecorder(Recorder):
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
        self.record_index('csi')

    def get_resp_data(self, resp: requests.Response):
        resp.raise_for_status()
        return resp.json()['list']

    def record_index(self, index_type):
        if index_type == 'csi':
            category_map_url = self.csi_category_map_url
        elif index_type == 'sh':
            category_map_url = self.sh_category_map_url
        else:
            self.logger.warning(f'not support index type: {index_type}')
            assert False

        requests_session = requests.Session()

        for category, url in category_map_url.items():
            resp = requests_session.get(url, headers=DEFAULT_HEADER)

            results = self.get_resp_data(resp)
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
                    'list_date': to_pd_timestamp(result['online_date']),
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


class ExchangeCSIndexStockRecorder(TimeSeriesDataRecorder):
    entity_provider = 'exchange'
    entity_schema = Index

    provider = 'exchange'
    data_schema = IndexStock

    original_page_url = 'http://www.csindex.com.cn/zh-CN/downloads/indices'
    url = 'http://www.csindex.com.cn/uploads/file/autofile/cons/{}cons.xls'

    def record(self, entity, start, end, size, timestamps):
        url = self.url.format(entity.code)
        response = requests.get(url, headers=DEFAULT_HEADER)
        response.raise_for_status()

        df = pd.read_excel(io.BytesIO(response.content))

        df = df[['日期Date', '成分券代码Constituent Code', '成分券名称Constituent Name']].rename(
            columns={'日期Date': 'timestamp', '成分券代码Constituent Code': 'stock_code',
                     '成分券名称Constituent Name': 'stock_name'})

        index_id = f'index_sh_{entity.code}'
        df['entity_id'] = index_id
        df['entity_type'] = 'index'
        df['exchange'] = 'sh'
        df['code'] = entity.code
        df['name'] = entity.name
        df['stock_id'] = df['stock_code'].apply(lambda x: china_stock_code_to_id(str(x)))
        # id format: {entity_id}_{timestamp}_{stock_id}
        df['id'] = df[['entity_id', 'timestamp', 'stock_id']].apply(lambda x: '_'.join(x.astype(str)), axis=1)
        df['timestamp'] = pd.to_datetime(df['timestamp'])

        df_to_db(data_schema=self.data_schema, df=df, provider=self.provider, force_update=True)


__all__ = ['ExchangeCSIndexMetaRecorder']

if __name__ == '__main__':
    # ExchangeIndexMetaRecorder().run()
    ExchangeCSIndexStockRecorder(codes=['000001']).run()
# the __all__ is generated
__all__ = ['ExchangeCSIndexMetaRecorder', 'ExchangeCSIndexStockRecorder']