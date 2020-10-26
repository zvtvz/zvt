# -*- coding: utf-8 -*-
import pandas as pd
from EmQuantAPI import *

from zvt.api import AdjustType, get_kdata, TIME_FORMAT_DAY, TIME_FORMAT_ISO8601, get_str_schema
from zvt.contract import IntervalLevel
from zvt.contract.api import df_to_db
from zvt.contract.recorder import TimeSeriesDataRecorder
from zvt.domain import RightsIssueDetail
from zvt.domain import StockDetail
from zvt.recorders.emquantapi.common import mainCallback, to_em_entity_id
from zvt.utils.pd_utils import pd_is_not_null
from zvt.utils.time_utils import now_pd_timestamp, to_time_str


class EmDividendDetailRecorder(TimeSeriesDataRecorder):
    entity_provider = 'joinquant'
    entity_schema = StockDetail

    # 数据来自jq
    provider = 'emquantapi'

    data_schema = RightsIssueDetail

    def __init__(self, entity_type='stock', exchanges=['sh', 'sz'], entity_ids=None, codes=None, batch_size=10,
                 force_update=False, sleeping_time=5, default_size=2000, real_time=False,
                 fix_duplicate_way='add', start_timestamp=None, end_timestamp=None, close_hour=0,
                 close_minute=0) -> None:
        self.data_schema = get_str_schema('RightsIssueDetail')
        super().__init__(entity_type, exchanges, entity_ids, codes, batch_size, force_update, sleeping_time,
                         default_size, real_time, fix_duplicate_way, start_timestamp, end_timestamp, close_hour,
                         close_minute)
        # 调用登录函数（激活后使用，不需要用户名密码）
        loginResult = c.start("ForceLogin=1", '', mainCallback)
        if (loginResult.ErrorCode != 0):
            print("login in fail")
            exit()

    def on_finish(self):
        # 退出
        loginresult = c.stop()
        if (loginresult.ErrorCode != 0):
            print("login in fail")
            exit()

    def record(self, entity, start, end, size, timestamps):
        if not end:
            end = to_time_str(now_pd_timestamp())
        start = to_time_str(start)
        reportdate_list = list({to_time_str(i)[:4] for i in pd.date_range(start, end)})
        em_code = to_em_entity_id(entity)
        df = pd.DataFrame()

        columns_dict = {
            "RTISSANNCDATE": "配股公告日",
            "RTISSREGISTDATE": "股权登记日",
            "RTISSEXDIVDATE": "配股除权日",
            "RTISSLISTDATE": "配股上市日",
            "RTISSPAYSDATE": "缴款起始日",
            "RTISSPAYEDATE": "缴款终止日",
            "RTISSPERTISSHARE": "每股配股数",
            "RTISSBASESHARES": "基准股本",
            "RTISSPLANNEDVOL": "计划配股数",
            "RTISSACTVOL": "实际配股数",
            "RTISSPRICE": "配股价格",
            "RTISSCOLLECTION": "配股募集资金",
            "RTISSNETCOLLECTION": "配股募集资金净额",
            "RTISSEXPENSE": "配股费用",

        }
        div_columns_list = list(columns_dict.keys())
        for reportdate in reportdate_list:
            # 方案
            div_df = c.css(em_code, div_columns_list,
                           "Year =" + reportdate + ",ispandas=1")

            df = df.append(div_df)
        df = df.dropna(subset=["RTISSEXDIVDATE"])
        df = df.sort_values("RTISSEXDIVDATE", ascending=True)
        if pd_is_not_null(df):
            df.reset_index(drop=True,inplace=True)
            df.rename(columns=self.data_schema.get_data_map(self), inplace=True)
            df['entity_id'] = entity.id
            df['timestamp'] = pd.to_datetime(df.rtiss_date)
            df['provider'] = 'emquantapi'
            df['code'] = entity.code

            def generate_id(se):
                return "{}_{}".format(se['entity_id'], to_time_str(se['timestamp'], fmt=TIME_FORMAT_DAY))

            df['id'] = df[['entity_id', 'timestamp']].apply(generate_id, axis=1)
            df_to_db(df=df, data_schema=self.data_schema, provider=self.provider, force_update=self.force_update)
        return None


__all__ = ['EmDividendDetailRecorder']

if __name__ == '__main__':
    # 上证50
    EmDividendDetailRecorder(codes=['050002']).run()
    # JqChinaEtfValuationRecorder(codes=['512290']).run()
