# -*- coding: utf-8 -*-
import time

import requests

from zvdata.domain import get_db_session
from zvdata.recorder import FixedCycleDataRecorder
from zvdata.structs import IntervalLevel
from zvt.api.technical import get_entities
from zvt.domain import IndexMoneyFlow, StockCategory, Index
from zvt.utils.time_utils import to_pd_timestamp
from zvt.utils.utils import to_float


# 实时资金流
# 'http://vip.stock.finance.sina.com.cn/quotes_service/api/json_v2.php/MoneyFlow.ssl_bkzj_bk?page=1&num=20&sort=netamount&asc=0&fenlei=1'
# 'http://vip.stock.finance.sina.com.cn/quotes_service/api/json_v2.php/MoneyFlow.ssl_bkzj_bk?page=1&num=20&sort=netamount&asc=0&fenlei=0'


class SinaIndexMoneyFlowRecorder(FixedCycleDataRecorder):
    entity_provider = 'sina'
    entity_schema = Index

    provider = 'sina'
    data_schema = IndexMoneyFlow

    url = 'http://vip.stock.finance.sina.com.cn/quotes_service/api/json_v2.php/MoneyFlow.ssl_bkzj_zjlrqs?page=1&num={}&sort=opendate&asc=0&bankuai={}%2F{}'

    def __init__(self, exchanges=['cn'], entity_ids=None, codes=None, batch_size=10,
                 force_update=False, sleeping_time=10, default_size=2000, one_shot=True, fix_duplicate_way='add',
                 start_timestamp=None, end_timestamp=None, contain_unfinished_data=False,
                 level=IntervalLevel.LEVEL_1DAY, kdata_use_begin_time=False, close_hour=15, close_minute=0,
                 one_day_trading_minutes=4 * 60) -> None:
        super().__init__('index', exchanges, entity_ids, codes, batch_size, force_update, sleeping_time,
                         default_size, one_shot, fix_duplicate_way, start_timestamp, end_timestamp,
                         contain_unfinished_data, level, kdata_use_begin_time, close_hour, close_minute,
                         one_day_trading_minutes)

    def init_entities(self):
        self.entity_session = get_db_session(provider=self.entity_provider, data_schema=self.entity_schema)

        self.entities = get_entities(session=self.entity_session, entity_type='index',
                                     exchanges=self.exchanges,
                                     codes=self.codes,
                                     entity_ids=self.entity_ids,
                                     return_type='domain', provider=self.provider,
                                     filters=[Index.category.in_(
                                         [StockCategory.industry.value, StockCategory.concept.value])])

    def generate_url(self, category, code, number):
        if category == StockCategory.industry.value:
            block = 0
        elif category == StockCategory.concept.value:
            block = 1

        return self.url.format(number, block, code)

    def get_data_map(self):
        return {}

    def record(self, entity, start, end, size, timestamps):
        url = self.generate_url(category=entity.category, code=entity.code, number=size)

        resp = requests.get(url)

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
            self.logger.error(resp.text)
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


if __name__ == '__main__':
    SinaIndexMoneyFlowRecorder(codes=['new_dzxx']).run()
    # SinaIndexMoneyFlowRecorder().run()
