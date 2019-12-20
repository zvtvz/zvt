# -*- coding: utf-8 -*-
import json

import demjson
import pandas as pd
import requests

from zvdata.api import df_to_db
from zvdata.recorder import Recorder
from zvt.api.common import china_stock_code_to_id
from zvt.api.quote import get_entities
from zvt.domain import StockIndex, StockCategory
from zvt.domain.meta.stock_meta import Index


class SinaChinaStockCategoryRecorder(Recorder):
    provider = 'sina'
    data_schema = StockIndex

    # 用于抓取行业/概念/地域列表
    category_map_url = {
        StockCategory.industry: 'http://vip.stock.finance.sina.com.cn/q/view/newSinaHy.php',
        StockCategory.concept: 'http://money.finance.sina.com.cn/q/view/newFLJK.php?param=class'
        # StockCategory.area: 'http://money.finance.sina.com.cn/q/view/newFLJK.php?param=area',
    }

    # 用于抓取行业包含的股票
    category_stocks_url = 'http://vip.stock.finance.sina.com.cn/quotes_service/api/json_v2.php/Market_Center.getHQNodeData?page={}&num=5000&sort=symbol&asc=1&node={}&symbol=&_s_r_a=page'

    def __init__(self, batch_size=10, force_update=False, sleeping_time=10) -> None:
        super().__init__(batch_size, force_update, sleeping_time)

        self.indices = get_entities(session=self.session, entity_type='index', exchanges=['cn'],
                                    return_type='domain', provider=self.provider)
        self.index_ids = [index_item.id for index_item in self.indices]

    def run(self):
        # get stock category from sina
        for category, url in self.category_map_url.items():
            resp = requests.get(url)
            resp.encoding = 'GBK'

            tmp_str = resp.text
            json_str = tmp_str[tmp_str.index('{'):tmp_str.index('}') + 1]
            tmp_json = json.loads(json_str)
            for code in tmp_json:
                name = tmp_json[code].split(',')[1]
                id = 'index_cn_{}'.format(code)
                if id in self.index_ids:
                    continue
                self.session.add(Index(id=id, entity_type='index', exchange='cn', code=code, name=name,
                                       category=category.value))
            self.session.commit()

        indices = get_entities(session=self.session, entity_type='index',
                               return_type='domain', filters=[
                Index.category.in_([StockCategory.industry.value, StockCategory.concept.value])],
                               provider=self.provider)

        for index_item in indices:
            for page in range(1, 5):
                resp = requests.get(self.category_stocks_url.format(page, index_item.code))
                try:
                    if resp.text == 'null' or resp.text is None:
                        break
                    category_jsons = demjson.decode(resp.text)
                    the_list = []
                    for category in category_jsons:
                        stock_code = category['code']
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
    # init_log('sina_china_stock_category.log')

    recorder = SinaChinaStockCategoryRecorder()
    recorder.run()
