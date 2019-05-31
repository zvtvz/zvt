# -*- coding: utf-8 -*-
import logging
import time

import requests

from zvt.domain import SecurityType, IndexMoneyFlow, StoreCategory, StockCategory, Provider, TradingLevel
from zvt.recorders.recorder import TimeSeriesFetchingStyle, FixedCycleDataRecorder, ApiWrapper
from zvt.utils.time_utils import to_pd_timestamp
from zvt.utils.utils import to_float

# 实时资金流
# 'http://vip.stock.finance.sina.com.cn/quotes_service/api/json_v2.php/MoneyFlow.ssl_bkzj_bk?page=1&num=20&sort=netamount&asc=0&fenlei=1'
# 'http://vip.stock.finance.sina.com.cn/quotes_service/api/json_v2.php/MoneyFlow.ssl_bkzj_bk?page=1&num=20&sort=netamount&asc=0&fenlei=0'

logger = logging.getLogger(__name__)


class MyApiWrapper(ApiWrapper):
    def request(self, url=None, method='post', param=None, path_fields=None):
        # security_item = param['security_item']

        resp = requests.get(param['url'])

        opendate = "opendate"
        avg_price = "avg_price"
        avg_changeratio = 'avg_changeratio'
        turnover = 'turnover'
        netamount = 'netamount'
        ratioamount = 'ratioamount'
        r0_net = 'r0_net'
        r0_ratio = 'r0_ratio'
        r0x_ratio = 'r0x_ratio'
        cnt_r0x_ratio = 'cnt_r0x_ratio'

        json_list = []
        try:
            json_list = eval(resp.text)
        except Exception as e:
            resp.encoding = 'GBK'
            logger.error(resp.text)
            time.sleep(60 * 5)

        result_list = []
        for item in json_list:
            result_list.append({
                'timestamp': to_pd_timestamp(item['opendate']),
                'close': to_float(item['avg_price']),
                'change_pct': to_float(item['avg_changeratio']),
                'turnover_rate': to_float(item['turnover']) / 10000,
                'net_inflows': to_float(item['netamount']),
                'net_inflow_rate': to_float(item['ratioamount']),
                'net_main_inflows': to_float(item['r0_net']),
                'net_main_inflow_rate': to_float(item['r0_ratio'])
            })

        return result_list


class SinaIndexMoneyFlowRecorder(FixedCycleDataRecorder):
    meta_provider = Provider.SINA
    provider = Provider.SINA

    data_schema = IndexMoneyFlow
    store_category = StoreCategory.money_flow
    url = 'http://vip.stock.finance.sina.com.cn/quotes_service/api/json_v2.php/MoneyFlow.ssl_bkzj_zjlrqs?page=1&num={}&sort=opendate&asc=0&bankuai={}%2F{}'
    api_wrapper = MyApiWrapper()

    def __init__(self, security_type=SecurityType.index, exchanges=['cn'], codes=None, batch_size=10,
                 force_update=False, sleeping_time=10, fetching_style=TimeSeriesFetchingStyle.end_size,
                 default_size=4000, contain_unfinished_data=False, level=TradingLevel.LEVEL_1DAY,
                 one_shot=True) -> None:
        super().__init__(security_type, exchanges, codes, batch_size, force_update, sleeping_time, fetching_style,
                         default_size, contain_unfinished_data, level, one_shot)

        # 只需要行业和概念
        self.securities = [item for item in self.securities if
                           (item.category == StockCategory.industry.value) or (
                                   item.category == StockCategory.concept.value)]

    def generate_url(self, category, code, number):
        if category == StockCategory.industry.value:
            block = 0
        elif category == StockCategory.concept.value:
            block = 1

        return self.url.format(number, block, code)

    def generate_request_param(self, security_item, start, end, size, timestamp):
        return {
            'url': self.generate_url(category=security_item.category, code=security_item.code, number=size),
            'security_item': security_item
        }

    def get_data_map(self):
        return {}


if __name__ == '__main__':
    # SinaIndexMoneyFlowRecorder(codes=['new_dzxx']).run()
    SinaIndexMoneyFlowRecorder().run()
