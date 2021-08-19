# -*- coding: utf-8 -*-
from typing import List

import pandas as pd
import requests

from zvt.api.utils import china_stock_code_to_id
from zvt.contract.api import df_to_db
from zvt.contract.recorder import Recorder, TimestampsDataRecorder
from zvt.domain import Index, IndexCategory, IndexStock
from zvt.recorders.consts import DEFAULT_HEADER
from zvt.utils.time_utils import now_pd_timestamp, to_pd_timestamp, to_time_str, TIME_FORMAT_MON


def get_resp_data(resp: requests.Response):
    resp.raise_for_status()
    return resp.json()['data']


class EastmoneyChinaIndexRecorder(Recorder):
    provider = 'eastmoney'
    data_schema = Index
    url = 'http://www.cnindex.net.cn/index/indexList?channelCode={}&rows=1000&pageNum=1'
    category_map_url = {
        IndexCategory.style: url.format('202'),
        IndexCategory.industry: url.format('201'),
        IndexCategory.scope: url.format('200'),
        IndexCategory.fund: url.format('207'),
    }

    def run(self):
        requests_session = requests.Session()

        for category, url in self.category_map_url.items():
            resp = requests_session.get(url, headers=DEFAULT_HEADER)

            results = get_resp_data(resp)['rows']
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
                index_info = get_resp_data(info_resp)
                name = result['indexname']
                entity_id = f'index_cn_{code}'
                index_item = {
                    'id': entity_id,
                    'entity_id': entity_id,
                    'timestamp': index_info['fbrq'],
                    'entity_type': 'index',
                    'exchange': 'cn',
                    'code': code,
                    'name': name,
                    'category': category.value,
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
            self.logger.info(f"finish record cnindex index:{category.value}")


class EastmoneyChinaIndexStockRecorder(TimestampsDataRecorder):
    entity_provider = 'eastmoney'
    entity_schema = Index

    provider = 'eastmoney'
    data_schema = IndexStock

    def init_timestamps(self, entity_item) -> List[pd.Timestamp]:
        return [to_pd_timestamp(item) for item in pd.date_range(entity_item.timestamp, now_pd_timestamp(), freq='M')]

    def record(self, entity, start, end, size, timestamps):
        for timestamp in timestamps:
            data_str = to_time_str(timestamp, TIME_FORMAT_MON)
            url = f'http://www.cnindex.net.cn/sample-detail/detail?indexcode={entity.code}&dateStr={data_str}&pageNum=1&rows=5000'
            resp = requests.get(url, headers=DEFAULT_HEADER)
            try:
                results = get_resp_data(resp)['rows']
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
                        'id': '{}_{}'.format(entity.id, stock_id),
                        'entity_id': entity.id,
                        'entity_type': entity.entity_type,
                        'exchange': entity.exchange,
                        'code': entity.code,
                        'name': entity.name,
                        'timestamp': now_pd_timestamp(),
                        'stock_id': stock_id,
                        'stock_code': stock_code,
                        'stock_name': stock_name
                    })
                if the_list:
                    df = pd.DataFrame.from_records(the_list)
                    df_to_db(data_schema=self.data_schema, df=df, provider=self.provider, force_update=True)

                self.logger.info('finish recording index:{},{}'.format(entity.category, entity.name))

            except Exception as e:
                self.logger.error("error:,resp.text:", e, resp.text)
            self.sleep()


__all__ = ['EastmoneyChinaIndexRecorder', 'EastmoneyChinaIndexStockRecorder']

if __name__ == '__main__':
    # init_log('china_stock_category.log')
    EastmoneyChinaIndexRecorder().run()

    recorder = EastmoneyChinaIndexStockRecorder(codes=['399370'])
    recorder.run()
