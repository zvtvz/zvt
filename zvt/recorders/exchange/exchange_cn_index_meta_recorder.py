# -*- coding: utf-8 -*-
from typing import List

import pandas as pd
import requests

from zvt.api.utils import china_stock_code_to_id, value_to_pct, value_multiply
from zvt.contract.api import df_to_db
from zvt.contract.recorder import Recorder, TimestampsDataRecorder
from zvt.domain import Index, IndexCategory, IndexStock
from zvt.recorders.consts import DEFAULT_HEADER
from zvt.utils.time_utils import to_pd_timestamp, to_time_str, TIME_FORMAT_MON, pre_month


# 深证指数，国证指数
class ExchangeCNIndexRecorder(Recorder):
    provider = 'exchange'
    data_schema = Index
    original_page_url = 'http://www.cnindex.com.cn/zh_indices/sese/index.html?act_menu=1&index_type=-1'
    url = 'http://www.cnindex.net.cn/index/indexList?channelCode={}&rows=1000&pageNum=1'

    # 中证指数 抓取 风格指数 行业指数 规模指数 基金指数
    cni_category_map_url = {
        IndexCategory.style: url.format('202'),
        IndexCategory.industry: url.format('201'),
        IndexCategory.scope: url.format('200'),
        IndexCategory.fund: url.format('207'),
    }

    # 深证指数 只取规模指数
    sz_category_map_url = {
        IndexCategory.scope: url.format('100'),
    }

    def run(self):
        self.record_index('sz')
        self.record_index('cni')

    def get_resp_data(self, resp: requests.Response):
        resp.raise_for_status()
        return resp.json()['data']

    def record_index(self, index_type):
        if index_type == 'cni':
            category_map_url = self.cni_category_map_url
        elif index_type == 'sz':
            category_map_url = self.sz_category_map_url
        else:
            self.logger.error(f'not support index_type: {index_type}')
            assert False

        requests_session = requests.Session()

        for category, url in category_map_url.items():
            resp = requests_session.get(url, headers=DEFAULT_HEADER)

            results = self.get_resp_data(resp)['rows']
            # e.g
            # amount: 277743699997.9
            # closeingPoint: 6104.7592
            # docchannel: 1039
            # freeMarketValue: 10794695531696.15
            # id: 142
            # indexcode: "399370"
            # indexename: "CNI Growth"
            # indexfullcname: "国证1000成长指数"
            # indexfullename: "CNI 1000 Growth Index"
            # indexname: "国证成长"
            # indexsource: "1"
            # indextype: "202"
            # pb: 5.34
            # peDynamic: 29.8607
            # peStatic: 33.4933
            # percent: 0.0022
            # prefixmonth: null
            # realtimemarket: "1"
            # remark: ""
            # sampleshowdate: null
            # samplesize: 332
            # showcnindex: "1"
            # totalMarketValue: 23113641352198.32
            the_list = []

            self.logger.info(f'category: {category} ')
            self.logger.info(f'results: {results} ')
            for i, result in enumerate(results):
                self.logger.info(f'to {i}/{len(results)}')
                code = result['indexcode']
                info_resp = requests_session.get(f'http://www.cnindex.net.cn/index-intro?indexcode={code}')
                # fbrq: "2010-01-04"
                # jd: 1000
                # jr: "2002-12-31"
                # jsfs: "自由流通市值"
                # jsjj: "国证成长由国证1000指数样本股中成长风格突出的股票组成，为投资者提供更丰富的指数化投资工具。"
                # qzsx: null
                # typl: 2
                # xyfw: "沪深A股"
                # xygz: "在国证1000指数样本股中，选取主营业务收入增长率、净利润增长率和净资产收益率综合排名前332只"
                index_info = self.get_resp_data(info_resp)
                name = result['indexname']
                entity_id = f'index_sz_{code}'
                index_item = {
                    'id': entity_id,
                    'entity_id': entity_id,
                    'timestamp': to_pd_timestamp(index_info['jr']),
                    'entity_type': 'index',
                    'exchange': 'sz',
                    'code': code,
                    'name': name,
                    'category': category.value,
                    'list_date': to_pd_timestamp(index_info['fbrq']),
                    'base_point': index_info['jd'],
                    'publisher': 'cnindex'
                }
                self.logger.info(index_item)
                the_list.append(index_item)
                self.sleep(2)
            if the_list:
                df = pd.DataFrame.from_records(the_list)
                df_to_db(data_schema=self.data_schema, df=df, provider=self.provider,
                         force_update=True)
            self.logger.info(f"finish record {index_type} index:{category.value}")


class ExchangeCNIndexStockRecorder(TimestampsDataRecorder):
    entity_provider = 'exchange'
    entity_schema = Index

    provider = 'exchange'
    data_schema = IndexStock

    original_page_url = 'http://www.cnindex.com.cn/module/index-detail.html?act_menu=1&indexCode=399001'
    url = 'http://www.cnindex.net.cn/sample-detail/detail?indexcode={}&dateStr={}&pageNum=1&rows=5000'

    def __init__(self,
                 force_update=False,
                 sleeping_time=5,
                 exchanges=None,
                 entity_ids=None,
                 code=None,
                 codes=None,
                 day_data=False,
                 entity_filters=None,
                 ignore_failed=True,
                 real_time=False,
                 fix_duplicate_way='add',
                 start_timestamp=None,
                 end_timestamp=None,
                 record_history=False) -> None:
        super().__init__(force_update, sleeping_time, exchanges, entity_ids, code, codes, day_data, entity_filters,
                         ignore_failed, real_time, fix_duplicate_way, start_timestamp, end_timestamp)
        self.record_history = record_history

    def init_timestamps(self, entity_item) -> List[pd.Timestamp]:
        last_valid_date = pre_month()
        if self.record_history:
            # 每个月记录一次
            return [to_pd_timestamp(item) for item in
                    pd.date_range(entity_item.list_date, last_valid_date, freq='M')]
        else:
            return [last_valid_date]

    def get_resp_data(self, resp: requests.Response):
        resp.raise_for_status()
        return resp.json()['data']

    def record(self, entity, start, end, size, timestamps):
        for timestamp in timestamps:
            data_str = to_time_str(timestamp, TIME_FORMAT_MON)
            resp = requests.get(self.url.format(entity.code, data_str), headers=DEFAULT_HEADER)
            results = self.get_resp_data(resp)['rows']
            if not results:
                self.logger.warning(f'no data for timestamp: {data_str}')
                self.sleep(3)
                continue
            the_list = []
            for result in results:
                # date: 1614268800000
                # dateStr: "2021-02-26"
                # freeMarketValue: 10610.8
                # indexcode: "399370"
                # market: null
                # seccode: "600519"
                # secname: "贵州茅台"
                # totalMarketValue: 26666.32
                # trade: "主要消费"
                # weight: 10.01
                stock_code = result['indexcode']
                stock_name = result['secname']
                stock_id = china_stock_code_to_id(stock_code)

                the_list.append({
                    'id': '{}_{}_{}'.format(entity.id, result['dateStr'], stock_id),
                    'entity_id': entity.id,
                    'entity_type': entity.entity_type,
                    'exchange': entity.exchange,
                    'code': entity.code,
                    'name': entity.name,
                    'timestamp': to_pd_timestamp(result['dateStr']),
                    'stock_id': stock_id,
                    'stock_code': stock_code,
                    'stock_name': stock_name,
                    'proportion': value_to_pct(result['weight'], 0),
                    'market_cap': value_multiply(result['freeMarketValue'], 100000000, 0)
                })
            if the_list:
                df = pd.DataFrame.from_records(the_list)
                df_to_db(data_schema=self.data_schema, df=df, provider=self.provider, force_update=True)

            self.logger.info(f'finish recording index:{entity.id}, {entity.name}, {data_str}')

            self.sleep(3)


if __name__ == '__main__':
    # init_log('china_stock_category.log')
    # ExchangeCNIndexRecorder().run()

    recorder = ExchangeCNIndexStockRecorder(codes=['399370'])
    recorder.run()
# the __all__ is generated
__all__ = ['ExchangeCNIndexRecorder', 'ExchangeCNIndexStockRecorder']
