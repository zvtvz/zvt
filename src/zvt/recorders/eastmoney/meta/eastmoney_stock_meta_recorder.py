# -*- coding: utf-8 -*-

import requests

from zvt.contract.api import get_entities
from zvt.contract.recorder import Recorder
from zvt.domain.meta.stock_meta import StockDetail, Stock
from zvt.recorders.exchange.exchange_stock_meta_recorder import ExchangeStockMetaRecorder
from zvt.utils.time_utils import to_pd_timestamp
from zvt.utils.utils import to_float, pct_to_float


class EastmoneyStockRecorder(ExchangeStockMetaRecorder):
    data_schema = Stock
    provider = "eastmoney"


class EastmoneyStockDetailRecorder(Recorder):
    provider = "eastmoney"
    data_schema = StockDetail

    def __init__(self, force_update=False, sleeping_time=5, code=None, codes=None) -> None:
        super().__init__(force_update, sleeping_time)

        # get list at first
        EastmoneyStockRecorder().run()

        if codes is None and code is not None:
            self.codes = [code]
        else:
            self.codes = codes
        filters = None
        if not self.force_update:
            filters = [StockDetail.profile.is_(None)]
        self.entities = get_entities(
            session=self.session,
            entity_schema=StockDetail,
            exchanges=None,
            codes=self.codes,
            filters=filters,
            return_type="domain",
            provider=self.provider,
        )

    def run(self):
        for security_item in self.entities:
            assert isinstance(security_item, StockDetail)

            if security_item.exchange == "sh":
                fc = "{}01".format(security_item.code)
            if security_item.exchange == "sz":
                fc = "{}02".format(security_item.code)

            # 基本资料
            # param = {"color": "w", "fc": fc, "SecurityCode": "SZ300059"}

            securities_code = f"{security_item.code}.{security_item.exchange.upper()}"
            param = {
                "type": "RPT_F10_ORG_BASICINFO",
                "sty": "ORG_PROFIE,MAIN_BUSINESS,FOUND_DATE,EM2016,BLGAINIAN,REGIONBK",
                "filter": f"(SECUCODE=\"{securities_code}\")",
                "client": "app",
                "source": "SECURITIES",
                "pageNumber": 1,
                "pageSize": 1
            }
            resp = requests.get("https://datacenter.eastmoney.com/securities/api/data/get", params=param)
            resp.encoding = "utf8"

            resp_json = resp.json()["result"]["data"][0]

            security_item.profile = resp_json["ORG_PROFIE"]
            security_item.main_business = resp_json["MAIN_BUSINESS"]
            security_item.date_of_establishment = to_pd_timestamp(resp_json["FOUND_DATE"])

            # 关联行业
            industries = ",".join(resp_json["EM2016"].split("-"))
            security_item.industries = industries

            # 关联概念
            security_item.concept_indices = resp_json["BLGAINIAN"]

            # 关联地区
            security_item.area_indices = resp_json["REGIONBK"]

            self.sleep()

            # 发行相关
            param = {
                "reportName": "RPT_F10_ORG_ISSUEINFO",
                "columns": "AFTER_ISSUE_PE,ISSUE_PRICE,TOTAL_ISSUE_NUM,NET_RAISE_FUNDS,ONLINE_ISSUE_LWR",
                "filter": f"(SECUCODE=\"{securities_code}\")(TYPENEW=\"4\")",
                "client": "app",
                "source": "SECURITIES",
                "pageNumber": 1,
                "pageSize": 1
            }
            resp = requests.get("https://datacenter.eastmoney.com/securities/api/data/v1/get", params=param)
            resp.encoding = "utf8"

            resp_json = resp.json()["result"]["data"][0]

            security_item.issue_pe = resp_json["AFTER_ISSUE_PE"]
            security_item.price = resp_json["ISSUE_PRICE"]
            security_item.issues = resp_json["TOTAL_ISSUE_NUM"]
            security_item.raising_fund = resp_json.get("NET_RAISE_FUNDS")
            security_item.net_winning_rate = resp_json["ONLINE_ISSUE_LWR"]

            self.session.commit()

            self.logger.info("finish recording stock meta for:{}".format(security_item.code))

            self.sleep()


if __name__ == "__main__":
    # init_log('china_stock_meta.log')

    recorder = EastmoneyStockRecorder()
    recorder.run()
    StockDetail.record_data(codes=["000338", "000777"], provider="eastmoney")


# the __all__ is generated
__all__ = ["EastmoneyStockRecorder", "EastmoneyStockDetailRecorder"]
