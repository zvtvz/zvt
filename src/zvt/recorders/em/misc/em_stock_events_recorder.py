# -*- coding: utf-8 -*-
import pandas as pd

from zvt.contract.api import df_to_db
from zvt.contract.recorder import FixedCycleDataRecorder
from zvt.domain import Stock
from zvt.domain.misc.stock_events import StockEvents
from zvt.domain.misc.stock_news import StockNews
from zvt.recorders.em import em_api
from zvt.utils import to_pd_timestamp, count_interval, now_pd_timestamp


class EMStockEventsRecorder(FixedCycleDataRecorder):
    original_page_url = (
        "https://emh5.eastmoney.com/html/detail.html?fc=300684.SZ&shareFlag=1&color=w&appfenxiang=1#/gsds"
    )
    url = "https://datacenter.eastmoney.com/securities/api/data/get?type=RTP_F10_DETAIL&params=300684.SZ&source=SECURITIES&client=APP&p=1&v=05132741154833669"

    entity_schema = Stock
    data_schema = StockEvents
    entity_provider = "em"
    provider = "em"

    def record(self, entity, start, end, size, timestamps):
        if not start:
            start = to_pd_timestamp("2005-01-01")
        days = count_interval(start, now_pd_timestamp())
        if days < 0:
            fetch_count = 1
        elif days <= 10:
            fetch_count = 3
        elif days <= 30:
            fetch_count = 5
        else:
            fetch_count = 2000

        stock_events = em_api.get_events(entity_id=entity.id, fetch_count=fetch_count)
        if stock_events:
            df = pd.DataFrame.from_records(stock_events)
            self.logger.info(df.head())
            df_to_db(df=df, data_schema=self.data_schema, provider=self.provider, force_update=self.force_update)


if __name__ == "__main__":
    r = EMStockEventsRecorder(entity_ids=["stock_sz_000338"], sleeping_time=0)
    r.run()
# the __all__ is generated
__all__ = ["EMStockEventsRecorder"]
