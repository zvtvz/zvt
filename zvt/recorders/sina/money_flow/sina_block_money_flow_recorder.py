# -*- coding: utf-8 -*-
import time

import requests

from zvt.contract.recorder import FixedCycleDataRecorder
from zvt.domain import BlockMoneyFlow, BlockCategory, Block
from zvt.utils.time_utils import to_pd_timestamp
from zvt.utils.utils import to_float


# 实时资金流
# 'http://vip.stock.finance.sina.com.cn/quotes_service/api/json_v2.php/MoneyFlow.ssl_bkzj_bk?page=1&num=20&sort=netamount&asc=0&fenlei=1'
# 'http://vip.stock.finance.sina.com.cn/quotes_service/api/json_v2.php/MoneyFlow.ssl_bkzj_bk?page=1&num=20&sort=netamount&asc=0&fenlei=0'


class SinaBlockMoneyFlowRecorder(FixedCycleDataRecorder):
    # entity的信息从哪里来
    entity_provider = "sina"
    # entity的schema
    entity_schema = Block

    # 记录的信息从哪里来
    provider = "sina"
    # 记录的schema
    data_schema = BlockMoneyFlow

    url = "http://vip.stock.finance.sina.com.cn/quotes_service/api/json_v2.php/MoneyFlow.ssl_bkzj_zjlrqs?page=1&num={}&sort=opendate&asc=0&bankuai={}%2F{}"

    def generate_url(self, category, code, number):
        if category == BlockCategory.industry.value:
            block = 0
        elif category == BlockCategory.concept.value:
            block = 1

        return self.url.format(number, block, code)

    def get_data_map(self):
        return {}

    def record(self, entity, start, end, size, timestamps):
        url = self.generate_url(category=entity.category, code=entity.code, number=size)

        resp = requests.get(url)

        opendate = "opendate"
        avg_price = "avg_price"
        avg_changeratio = "avg_changeratio"
        turnover = "turnover"
        netamount = "netamount"
        ratioamount = "ratioamount"
        r0_net = "r0_net"
        r0_ratio = "r0_ratio"
        r0x_ratio = "r0x_ratio"
        cnt_r0x_ratio = "cnt_r0x_ratio"

        json_list = []
        try:
            json_list = eval(resp.text)
        except Exception as e:
            resp.encoding = "GBK"
            self.logger.error(resp.text)
            time.sleep(60 * 5)

        result_list = []
        for item in json_list:
            result_list.append(
                {
                    "name": entity.name,
                    "timestamp": to_pd_timestamp(item["opendate"]),
                    "close": to_float(item["avg_price"]),
                    "change_pct": to_float(item["avg_changeratio"]),
                    "turnover_rate": to_float(item["turnover"]) / 10000,
                    "net_inflows": to_float(item["netamount"]),
                    "net_inflow_rate": to_float(item["ratioamount"]),
                    "net_main_inflows": to_float(item["r0_net"]),
                    "net_main_inflow_rate": to_float(item["r0_ratio"]),
                }
            )

        return result_list


if __name__ == "__main__":
    SinaBlockMoneyFlowRecorder(codes=["new_fjzz"]).run()
    # SinaIndexMoneyFlowRecorder().run()
# the __all__ is generated
__all__ = ["SinaBlockMoneyFlowRecorder"]
