# -*- coding: utf-8 -*-
import pandas as pd
import requests

from zvt.contract.api import df_to_db
from zvt.contract.recorder import Recorder, TimeSeriesDataRecorder
from zvt.utils.time_utils import now_pd_timestamp
from zvt.utils.utils import json_callback_param
from zvt.api.quote import china_stock_code_to_id
from zvt.domain import BlockStock, BlockCategory, Block


class EastmoneyChinaBlockRecorder(Recorder):
    provider = 'eastmoney'
    data_schema = Block

    # 用于抓取行业/概念/地域列表
    category_map_url = {
        BlockCategory.industry: 'https://nufm.dfcfw.com/EM_Finance2014NumericApplication/JS.aspx?type=CT&cmd=C._BKHY&sty=DCRRBKCPAL&st=(ChangePercent)&sr=-1&p=1&ps=200&lvl=&cb=jsonp_F1A61014DE5E45B7A50068EA290BC918&token=4f1862fc3b5e77c150a2b985b12db0fd&_=08766',
        BlockCategory.concept: 'https://nufm.dfcfw.com/EM_Finance2014NumericApplication/JS.aspx?type=CT&cmd=C._BKGN&sty=DCRRBKCPAL&st=(ChangePercent)&sr=-1&p=1&ps=300&lvl=&cb=jsonp_3071689CC1E6486A80027D69E8B33F26&token=4f1862fc3b5e77c150a2b985b12db0fd&_=08251',
        # BlockCategory.area: 'https://nufm.dfcfw.com/EM_Finance2014NumericApplication/JS.aspx?type=CT&cmd=C._BKDY&sty=DCRRBKCPAL&st=(ChangePercent)&sr=-1&p=1&ps=200&lvl=&cb=jsonp_A597D4867B3D4659A203AADE5B3B3AD5&token=4f1862fc3b5e77c150a2b985b12db0fd&_=02443'
    }

    def run(self):
        for category, url in self.category_map_url.items():
            resp = requests.get(url)
            results = json_callback_param(resp.text)
            the_list = []
            for result in results:
                items = result.split(',')
                code = items[1]
                name = items[2]
                entity_id = f'block_cn_{code}'
                the_list.append({
                    'id': entity_id,
                    'entity_id': entity_id,
                    'entity_type': 'block',
                    'exchange': 'cn',
                    'code': code,
                    'name': name,
                    'category': category.value
                })
            if the_list:
                df = pd.DataFrame.from_records(the_list)
                df_to_db(data_schema=self.data_schema, df=df, provider=self.provider,
                         force_update=True)
            self.logger.info(f"finish record sina blocks:{category.value}")


class EastmoneyChinaBlockStockRecorder(TimeSeriesDataRecorder):
    entity_provider = 'eastmoney'
    entity_schema = Block

    provider = 'eastmoney'
    data_schema = BlockStock

    # 用于抓取行业包含的股票
    category_stocks_url = 'https://nufm.dfcfw.com/EM_Finance2014NumericApplication/JS.aspx?type=CT&cmd=C.{}{}&sty=SFCOO&st=(Close)&sr=-1&p=1&ps=300&cb=jsonp_B66B5BAA1C1B47B5BB9778045845B947&token=7bc05d0d4c3c22ef9fca8c2a912d779c'

    def __init__(self, exchanges=None, entity_ids=None, codes=None, day_data=False, batch_size=10,
                 force_update=False, sleeping_time=5, default_size=2000, real_time=False, fix_duplicate_way='add',
                 start_timestamp=None, end_timestamp=None, close_hour=0, close_minute=0) -> None:
        super().__init__('block', exchanges, entity_ids, codes, day_data, batch_size, force_update, sleeping_time,
                         default_size, real_time, fix_duplicate_way, start_timestamp, end_timestamp, close_hour,
                         close_minute)

    def record(self, entity, start, end, size, timestamps):
        resp = requests.get(self.category_stocks_url.format(entity.code, '1'))
        try:
            results = json_callback_param(resp.text)
            the_list = []
            for result in results:
                items = result.split(',')
                stock_code = items[1]
                stock_id = china_stock_code_to_id(stock_code)
                block_id = entity.id

                the_list.append({
                    'id': '{}_{}'.format(block_id, stock_id),
                    'entity_id': block_id,
                    'entity_type': 'block',
                    'exchange': entity.exchange,
                    'code': entity.code,
                    'name': entity.name,
                    'timestamp': now_pd_timestamp(),
                    'stock_id': stock_id,
                    'stock_code': stock_code,
                    'stock_name': items[2],

                })
            if the_list:
                df = pd.DataFrame.from_records(the_list)
                df_to_db(data_schema=self.data_schema, df=df, provider=self.provider, force_update=True)

            self.logger.info('finish recording block:{},{}'.format(entity.category, entity.name))

        except Exception as e:
            self.logger.error("error:,resp.text:", e, resp.text)
        self.sleep()


__all__ = ['EastmoneyChinaBlockRecorder', 'EastmoneyChinaBlockStockRecorder']

if __name__ == '__main__':
    # init_log('china_stock_category.log')

    recorder = EastmoneyChinaBlockStockRecorder(codes=['BK0727'])
    recorder.run()
