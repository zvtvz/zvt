# -*- coding: utf-8 -*-
import pandas as pd
import requests

from zvdata.api import df_to_db
from zvdata.recorder import Recorder
from zvt.api.common import china_stock_code_to_id
from zvt.api.quote import get_entities
from zvt.domain import StockIndex, StockCategory
from zvt.domain.meta.stock_meta import Index
from zvdata.utils.utils import json_callback_param


class ChinaStockCategoryRecorder(Recorder):
    provider = 'eastmoney'
    data_schema = StockIndex

    # 用于抓取行业/概念/地域列表
    category_map_url = {
        StockCategory.industry: 'https://nufm.dfcfw.com/EM_Finance2014NumericApplication/JS.aspx?type=CT&cmd=C._BKHY&sty=DCRRBKCPAL&st=(ChangePercent)&sr=-1&p=1&ps=200&lvl=&cb=jsonp_F1A61014DE5E45B7A50068EA290BC918&token=4f1862fc3b5e77c150a2b985b12db0fd&_=08766',
        StockCategory.concept: 'https://nufm.dfcfw.com/EM_Finance2014NumericApplication/JS.aspx?type=CT&cmd=C._BKGN&sty=DCRRBKCPAL&st=(ChangePercent)&sr=-1&p=1&ps=300&lvl=&cb=jsonp_3071689CC1E6486A80027D69E8B33F26&token=4f1862fc3b5e77c150a2b985b12db0fd&_=08251',
        StockCategory.area: 'https://nufm.dfcfw.com/EM_Finance2014NumericApplication/JS.aspx?type=CT&cmd=C._BKDY&sty=DCRRBKCPAL&st=(ChangePercent)&sr=-1&p=1&ps=200&lvl=&cb=jsonp_A597D4867B3D4659A203AADE5B3B3AD5&token=4f1862fc3b5e77c150a2b985b12db0fd&_=02443'
    }

    # 用于抓取行业包含的股票
    category_stocks_url = 'https://nufm.dfcfw.com/EM_Finance2014NumericApplication/JS.aspx?type=CT&cmd=C.{}{}&sty=SFCOO&st=(Close)&sr=-1&p=1&ps=300&cb=jsonp_B66B5BAA1C1B47B5BB9778045845B947&token=7bc05d0d4c3c22ef9fca8c2a912d779c'

    def __init__(self, batch_size=10, force_update=False, sleeping_time=10) -> None:
        super().__init__(batch_size, force_update, sleeping_time)

        self.indices = get_entities(session=self.session, entity_type='index', exchanges=['cn'],
                                    return_type='domain', provider=self.provider)
        self.index_ids = [index_item.id for index_item in self.indices]

    def run(self):
        for category, url in self.category_map_url.items():
            resp = requests.get(url)
            results = json_callback_param(resp.text)
            for result in results:
                items = result.split(',')
                code = items[1]
                name = items[2]
                id = 'index_cn_{}'.format(code)
                if id in self.index_ids:
                    continue
                self.session.add(Index(id=id, entity_id=id, entity_type='index', exchange='cn', code=code, name=name,
                                       category=category.value))
            self.session.commit()

        indices = get_entities(session=self.session, entity_type='index',
                               return_type='domain', filters=[
                Index.category.in_(
                    [StockCategory.concept.value, StockCategory.industry.value])],
                               provider=self.provider)

        for index_item in indices:
            resp = requests.get(self.category_stocks_url.format(index_item.code, '1'))
            try:
                results = json_callback_param(resp.text)
                the_list = []
                for result in results:
                    items = result.split(',')
                    stock_code = items[1]
                    stock_id = china_stock_code_to_id(stock_code)
                    index_id = index_item.id
                    the_list.append({
                        'id': '{}_{}'.format(index_id, stock_id),
                        'index_id': index_id,
                        'stock_id': stock_id
                    })
                if the_list:
                    df = pd.DataFrame.from_records(the_list)
                    df_to_db(data_schema=self.data_schema, df=df, provider=self.provider)

                self.logger.info('finish recording index:{},{}'.format(index_item.category, index_item.name))

            except Exception as e:
                self.logger.error("error:,resp.text:", e, resp.text)
            self.sleep()


if __name__ == '__main__':
    # init_log('china_stock_category.log')

    recorder = ChinaStockCategoryRecorder()
    recorder.run()
