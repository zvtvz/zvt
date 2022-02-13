# -*- coding: utf-8 -*-
import pandas as pd

from zvt.contract.api import df_to_db
from zvt.contract.recorder import FixedCycleDataRecorder
from zvt.domain import Stock
from zvt.domain.misc.stock_news import StockNews
from zvt.recorders.em import em_api


class EMStockNewsRecorder(FixedCycleDataRecorder):
    original_page_url = "https://wap.eastmoney.com/quote/stock/0.002572.html"
    url = "https://np-listapi.eastmoney.com/comm/wap/getListInfo?cb=callback&client=wap&type=1&mTypeAndCode=0.002572&pageSize=200&pageIndex={}&callback=jQuery1830017478247906740352_1644568731256&_=1644568879493"

    entity_schema = Stock
    data_schema = StockNews
    entity_provider = "em"
    provider = "em"

    def record(self, entity, start, end, size, timestamps):
        news = em_api.get_news(entity_id=entity.id)
        df = pd.DataFrame.from_records(news)
        self.logger.info(df)
        df_to_db(df=df, data_schema=self.data_schema, provider=self.provider, force_update=self.force_update)


if __name__ == "__main__":
    r = EMStockNewsRecorder(entity_ids=["stock_sz_300999"])
    r.run()
# the __all__ is generated
__all__ = ["EMStockNewsRecorder"]
