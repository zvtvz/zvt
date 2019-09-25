# -*- coding: utf-8 -*-
import time

import requests

from zvdata import IntervalLevel
from zvdata.recorder import FixedCycleDataRecorder
from zvdata.utils.time_utils import to_pd_timestamp
from zvdata.utils.utils import to_float
from zvt.domain import StockMoneyFlow, Stock


class SinaStockMoneyFlowRecorder(FixedCycleDataRecorder):
    entity_provider = 'sina'
    entity_schema = Stock

    provider = 'sina'
    data_schema = StockMoneyFlow

    url = 'http://vip.stock.finance.sina.com.cn/quotes_service/api/json_v2.php/MoneyFlow.ssl_qsfx_lscjfb?page=1&num={}&sort=opendate&asc=0&daima={}'

    def __init__(self, entity_type='stock', exchanges=['sh', 'sz'], entity_ids=None, codes=None, batch_size=10,
                 force_update=False, sleeping_time=10, default_size=4000, real_time=True, fix_duplicate_way='add',
                 start_timestamp=None, end_timestamp=None,
                 level=IntervalLevel.LEVEL_1DAY, kdata_use_begin_time=False, close_hour=15, close_minute=0,
                 one_day_trading_minutes=4 * 60) -> None:

        super().__init__(entity_type, exchanges, entity_ids, codes, batch_size, force_update, sleeping_time,
                         default_size, real_time, fix_duplicate_way, start_timestamp, end_timestamp, close_hour,
                         close_minute, level, kdata_use_begin_time,
                         one_day_trading_minutes)

    def generate_url(self, code, number):
        return self.url.format(number, code)

    def get_data_map(self):
        return {}

    def record(self, entity, start, end, size, timestamps):
        param = {
            'url': self.generate_url(code='{}{}'.format(entity.exchange, entity.code), number=size),
            'security_item': entity
        }

        resp = requests.get(param['url'])
        # {opendate:"2019-04-29",trade:"10.8700",changeratio:"-0.0431338",turnover:"74.924",netamount:"-2903349.8500",
        # ratioamount:"-0.155177",r0:"0.0000",r1:"2064153.0000",r2:"6485031.0000",r3:"10622169.2100",r0_net:"0.0000",
        # r1_net:"2064153.0000",r2_net:"-1463770.0000",r3_net:"-3503732.8500"}
        opendate = "opendate"
        trade = "trade"
        changeratio = 'changeratio'
        turnover = 'turnover'
        netamount = 'netamount'
        ratioamount = 'ratioamount'
        r0 = 'r0'
        r1 = 'r1'
        r2 = 'r2'
        r3 = 'r3'
        r0_net = 'r0_net'
        r1_net = 'r1_net'
        r2_net = 'r2_net'
        r3_net = 'r3_net'

        json_list = []

        try:
            json_list = eval(resp.text)
        except Exception as e:
            resp.encoding = 'GBK'
            self.logger.error(resp.text)
            time.sleep(60 * 5)

        result_list = []
        for item in json_list:
            amount = to_float(item['r0']) + to_float(item['r1']) + to_float(item['r2']) + to_float(item['r3'])

            result = {
                'timestamp': to_pd_timestamp(item['opendate']),
                'close': to_float(item['trade']),
                'change_pct': to_float(item['changeratio']),
                'turnover_rate': to_float(item['turnover']) / 10000,
                'net_inflows': to_float(item['netamount']),
                'net_inflow_rate': to_float(item['ratioamount']),
                #     # 主力=超大单+大单
                #     net_main_inflows = Column(Float)
                #     net_main_inflow_rate = Column(Float)
                #     # 超大单
                #     net_huge_inflows = Column(Float)
                #     net_huge_inflow_rate = Column(Float)
                #     # 大单
                #     net_big_inflows = Column(Float)
                #     net_big_inflow_rate = Column(Float)
                #
                #     # 中单
                #     net_medium_inflows = Column(Float)
                #     net_medium_inflow_rate = Column(Float)
                #     # 小单
                #     net_small_inflows = Column(Float)
                #     net_small_inflow_rate = Column(Float)
                'net_main_inflows': to_float(item['r0_net']) + to_float(item['r1_net']),

                'net_huge_inflows': to_float(item['r0_net']),

                'net_big_inflows': to_float(item['r1_net']),

                'net_medium_inflows': to_float(item['r2_net']),

                'net_small_inflows': to_float(item['r3_net']),
            }

            if amount != 0:
                result['net_main_inflow_rate'] = (to_float(item['r0_net']) + to_float(item['r1_net'])) / amount
                result['net_huge_inflows_rate'] = to_float(item['r0_net']) / amount
                result['net_big_inflows_rate'] = to_float(item['r1_net']) / amount
                result['net_medium_inflows_rate'] = to_float(item['r2_net']) / amount
                result['net_small_inflows_rate'] = to_float(item['r3_net']) / amount

            result_list.append(result)

        return result_list


if __name__ == '__main__':
    SinaStockMoneyFlowRecorder(codes=['000338']).run()
    # SinaStockMoneyFlowRecorder().run()
