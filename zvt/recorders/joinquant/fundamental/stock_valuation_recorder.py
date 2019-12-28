# -*- coding: utf-8 -*-

import pandas as pd
from jqdatasdk import auth, logout, query, valuation, get_fundamentals_continuously

from zvdata.api import df_to_db
from zvdata.recorder import TimeSeriesDataRecorder
from zvdata.utils.time_utils import now_pd_timestamp, now_time_str
from zvt import zvt_env
from zvt.domain import Stock, Valuation
from zvt.recorders.joinquant import to_jq_entity_id


class ChinaStockValuationRecorder(TimeSeriesDataRecorder):
    # 复用eastmoney的股票列表
    entity_provider = 'eastmoney'
    entity_schema = Stock

    # 数据来自jq
    provider = 'joinquant'

    data_schema = Valuation

    def __init__(self, entity_type='stock', exchanges=['sh', 'sz'], entity_ids=None, codes=None, batch_size=10,
                 force_update=False, sleeping_time=5, default_size=2000, real_time=False, fix_duplicate_way='add',
                 start_timestamp=None, end_timestamp=None, close_hour=0, close_minute=0) -> None:
        super().__init__(entity_type, exchanges, entity_ids, codes, batch_size, force_update, sleeping_time,
                         default_size, real_time, fix_duplicate_way, start_timestamp, end_timestamp, close_hour,
                         close_minute)
        auth(zvt_env['jq_username'], zvt_env['jq_password'])

    def on_finish(self):
        super().on_finish()
        logout()

    def record(self, entity, start, end, size, timestamps):
        # 只要前复权数据
        q = query(
            valuation
        ).filter(
            valuation.code == to_jq_entity_id(entity)
        )
        count: pd.Timedelta = now_pd_timestamp() - start
        panel = get_fundamentals_continuously(q, end_date=now_time_str(), count=count.days + 1)
        if not panel.empty:
            print(panel)
            df = panel.to_frame()
            df_to_db(df=df, data_schema=self.data_schema, provider=self.provider, force_update=self.force_update)

        return None


if __name__ == '__main__':
    ChinaStockValuationRecorder(codes=['000001']).run()
