# -*- coding: utf-8 -*-
import pandas as pd

from zvt.contract.api import df_to_db
from zvt.contract.recorder import FixedCycleDataRecorder
from zvt.domain import Stock
from zvt.domain.misc.stock_news import StockNews
from zvt.recorders.em import em_api
from zvt.utils.time_utils import count_interval, now_pd_timestamp, recent_year_date


class EMStockNewsRecorder(FixedCycleDataRecorder):
    original_page_url = "https://wap.eastmoney.com/quote/stock/0.002572.html"
    url = "https://np-listapi.eastmoney.com/comm/wap/getListInfo?cb=callback&client=wap&type=1&mTypeAndCode=0.002572&pageSize=200&pageIndex={}&callback=jQuery1830017478247906740352_1644568731256&_=1644568879493"

    entity_schema = Stock
    data_schema = StockNews
    entity_provider = "em"
    provider = "em"

    def record(self, entity, start, end, size, timestamps):
        from_date = recent_year_date()
        if not start or (start < from_date):
            start = from_date

        if count_interval(start, now_pd_timestamp()) <= 30:
            ps = 30
        else:
            ps = 200

        latest_news: StockNews = self.get_latest_saved_record(entity=entity)

        news = em_api.get_news(
            session=self.http_session,
            entity_id=entity.id,
            ps=ps,
            start_timestamp=start,
            latest_code=latest_news.news_code if latest_news else None,
        )
        if news:
            df = pd.DataFrame.from_records(news)
            self.logger.info(df)
            df_to_db(df=df, data_schema=self.data_schema, provider=self.provider, force_update=self.force_update)


if __name__ == "__main__":
    # df = Stock.query_data(filters=[Stock.exchange == "bj"], provider="em")
    # entity_ids = df["entity_id"].tolist()
    r = EMStockNewsRecorder(entity_ids=["stock_sh_600345"], sleeping_time=0)
    r.run()


# the __all__ is generated
__all__ = ["EMStockNewsRecorder"]
