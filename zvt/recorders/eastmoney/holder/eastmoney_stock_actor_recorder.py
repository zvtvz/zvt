# -*- coding: utf-8 -*-
import requests

from zvt.api import get_recent_report_date
from zvt.contract.recorder import Recorder
from zvt.domain.actor.actor_meta import ActorMeta
from zvt.utils import to_pd_timestamp


class EastmoneyActorRecorder(Recorder):
    name = "eastmoney_actor_recorder"
    provider = "eastmoney"
    data_schema = ActorMeta

    url = "https://datacenter.eastmoney.com/securities/api/data/v1/get?reportName=RPT_FREEHOLDERS_BASIC_INFO&columns=HOLDER_NAME,END_DATE,HOLDER_NEW,HOLDER_NUM,HOLDER_CODE&quoteColumns=&filter=(END_DATE='{}')&pageNumber={}&pageSize={}&sortTypes=-1,-1&sortColumns=HOLDER_NUM,HOLDER_NAME&source=SECURITIES&client=SW"

    start = "2016-03-31"

    def get_data(self, end_date, pn, ps):
        resp = requests.get(url=self.url.format(end_date, pn, ps))
        return resp.json()

    def run(self):
        current_date = get_recent_report_date()
        pn = 1
        ps = 2000

        while to_pd_timestamp(current_date) >= to_pd_timestamp(self.start):
            if not self.state:
                current_date = get_recent_report_date()
                result = self.get_data(end_date=current_date, pn=pn, ps=ps)
                print(result)
                self.state = {"end_date": current_date, "pages": result["result"]["pages"], "pn": pn, "ps": ps}
                self.persist_state("stock_sz_000001", self.state)
            else:
                if self.state["pn"] >= self.state["pages"]:
                    current_date = get_recent_report_date(the_date=self.state["end_date"], step=1)
                    pn = pn
                    ps = ps
                else:
                    pn = self.state["pn"] + 1
                    ps = self.state["ps"]
                    current_date = self.state["end_date"]

                result = self.get_data(end_date=current_date, pn=pn, ps=ps)
                print(result)
                self.state = {"end_date": current_date, "pages": result["result"]["pages"], "pn": pn, "ps": ps}
                self.persist_state("stock_sz_000001", self.state)


if __name__ == "__main__":
    EastmoneyActorRecorder().run()
# the __all__ is generated
__all__ = ["EastmoneyActorRecorder"]
