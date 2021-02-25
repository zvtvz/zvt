# -*- coding: utf-8 -*-
import pandas as pd
from jqdatasdk import auth, logout, finance, query
from zvt.recorders.joinquant.common import to_jq_entity_id

from zvt import zvt_env
from zvt.api import TIME_FORMAT_DAY, get_str_schema
from zvt.contract.api import df_to_db
from zvt.contract.recorder import TimeSeriesDataRecorder
from zvt.domain import StockDetail,StockStatus

from zvt.utils.pd_utils import pd_is_not_null
from zvt.utils.time_utils import now_pd_timestamp, to_time_str

class JqChinaStockStatusRecorder(TimeSeriesDataRecorder):
    entity_provider = 'joinquant'
    entity_schema = StockDetail

    # 数据来自jq
    provider = 'joinquant'

    data_schema = StockStatus

    def __init__(self, entity_type='stock', exchanges=['sh', 'sz'], entity_ids=None, codes=None, batch_size=10,
                 force_update=False, sleeping_time=5, default_size=2000, real_time=False,
                 fix_duplicate_way='add', start_timestamp=None, end_timestamp=None, close_hour=0,
                 close_minute=0) -> None:
        self.data_schema = StockStatus
        super().__init__(entity_type, exchanges, entity_ids, codes, batch_size, force_update, sleeping_time,
                         default_size, real_time, fix_duplicate_way, start_timestamp, end_timestamp, close_hour,
                         close_minute)
        # 调用登录函数（激活后使用，不需要用户名密码）
        auth(zvt_env['jq_username'], zvt_env['jq_password'])

    def on_finish(self):
        super().on_finish()
        logout()

    def record(self, entity, start, end, size, timestamps):
        if not end:
            end = to_time_str(now_pd_timestamp())
        start = to_time_str(start)
        q = query(finance.STK_STATUS_CHANGE).filter(
            finance.STK_STATUS_CHANGE.code == to_jq_entity_id(entity)).filter(
            finance.STK_STATUS_CHANGE.pub_date >= to_time_str(start)).limit(10)
        df = finance.run_query(q)

        if pd_is_not_null(df):
            df['pub_date'] = pd.to_datetime(df['pub_date'])
            df['exchange'] = entity.exchange
            df['entity_type'] = entity.entity_type
            df['change_date'] = pd.to_datetime(df['change_date'])
            df['timestamp'] = df['change_date']

            df['entity_id'] = entity.id
            df['provider'] = 'joinquant'
            df['code'] = entity.code

            def generate_finance_id(se):
                return "{}_{}".format(se['entity_id'], to_time_str(se['timestamp'], fmt=TIME_FORMAT_DAY))

            df['id'] = df[['entity_id', 'timestamp']].apply(generate_finance_id, axis=1)

            df_to_db(df=df, data_schema=self.data_schema, provider=self.provider, force_update=self.force_update)
        return None

__all__ = ['JqChinaStockStatusRecorder']
