# -*- coding: utf-8 -*-
import pandas as pd
from EmQuantAPI import *

from zvt.api import AdjustType, get_kdata, TIME_FORMAT_DAY, TIME_FORMAT_ISO8601, get_str_schema
from zvt.contract import IntervalLevel
from zvt.contract.api import df_to_db
from zvt.contract.recorder import TimeSeriesDataRecorder
from zvt.domain import DividendDetail,StockDetail
from zvt.recorders.emquantapi.common import mainCallback, to_em_entity_id
from zvt.utils.pd_utils import pd_is_not_null
from zvt.utils.time_utils import now_pd_timestamp, to_time_str


class EmDividendDetailRecorder(TimeSeriesDataRecorder):
    entity_provider = 'joinquant'
    entity_schema = StockDetail


    provider = 'emquantapi'

    data_schema = DividendDetail

    def __init__(self, entity_type='stock', exchanges=['sh', 'sz'], entity_ids=None, codes=None, batch_size=10,
                 force_update=False, sleeping_time=5, default_size=2000, real_time=False,
                 fix_duplicate_way='add', start_timestamp=None, end_timestamp=None, close_hour=0,
                 close_minute=0) -> None:
        self.data_schema = get_str_schema('DividendDetail')
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
        reportdate_list = sorted(list({to_time_str(i)[:4] + '-12-31' for i in pd.date_range(start, end)}))
        em_code = to_em_entity_id(entity)
        df = pd.DataFrame()

        div_columns_dict = {
            "DIVAGMANNCDATE": "股东大会公告日",
            "DIVEXDATE": "除权除息日",
            "DIVRECORDDATE": "股权登记日",
            "DIVIMPLANNCDATE": "分红实施公告日",
            "DIVLASTTRDDATESHAREB": "B股最后交易日",
            "DIVCASHPSAFTAX": "每股股利(税后)",
            "DIVCASHPSBFTAX": "每股股利(税前)",
            "DIVPROGRESS": "分红方案进度",
            "DIVPAYDATE": "派息日",
            # "DIVCASHDATE": "最新现金分红报告期",
            "DIVSTOCKPS": "每股送股比例",
            "DIVCAPITALIZATIONPS": "每股转增比例",
            "DIVCASHANDSTOCKPS": "分红送转方案",
        }

        div_columns_list = [i for i in div_columns_dict.keys()]
        for reportdate in reportdate_list:
            # 方案
            div_df = c.css(em_code, div_columns_list,
                           "ReportDate =" + reportdate + ",ispandas=1,AssignFeature=1,YesNo=1")
            div_df['report_date'] = reportdate
            df = df.append(div_df)
        # df.rename(columns=div_columns_dict, inplace=True)
        df = df.dropna(subset=["DIVEXDATE"])
        df = df.sort_values("DIVEXDATE", ascending=True)
        df['DIVCASHPSAFTAX'] = df['DIVCASHPSAFTAX'].apply(lambda x:str(x).split('或')[0])
        df['DIVCASHANDSTOCKPS'] =  df['DIVCASHANDSTOCKPS'].apply(lambda x: str(x).split('（')[0])
        if pd_is_not_null(df):
            df.reset_index(drop=True,inplace=True)
            df.rename(columns=self.data_schema.get_data_map(self), inplace=True)
            df['dividend'] = df['dividend'].apply(lambda x: str(x).split('（')[0])
            df['entity_id'] = entity.id
            df['timestamp'] = pd.to_datetime(df.dividend_date)
            df['provider'] = 'emquantapi'
            df['code'] = entity.code

            def generate_id(se):
                return "{}_{}".format(se['entity_id'], to_time_str(se['timestamp'], fmt=TIME_FORMAT_DAY))

            df['id'] = df[['entity_id', 'timestamp']].apply(generate_id, axis=1)
            df.replace('None',pd.NaT,inplace=True)
            df_to_db(df=df, data_schema=self.data_schema, provider=self.provider, force_update=self.force_update)
        return None


# dividend_per_share_after_tax                     object
# dividend_per_share_before_tax                    object

# dividend_pay_date                                object
# share_bonus_per_share                            object
# per_share_conversion_ratio                       object

__all__ = ['EmDividendDetailRecorder']

if __name__ == '__main__':
    # 上证50
    EmDividendDetailRecorder(codes=['050002']).run()
    # JqChinaEtfValuationRecorder(codes=['512290']).run()
