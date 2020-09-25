# -*- coding: utf-8 -*-
import pandas as pd
from EmQuantAPI import *

from zvt.api import get_recent_report_period
from zvt.contract.api import df_to_db
from zvt.contract.recorder import TimeSeriesDataRecorder
from zvt.domain import StockDetail
from zvt.recorders.emquantapi.common import mainCallback, to_em_entity_id
from zvt.utils.pd_utils import pd_is_not_null
from zvt.utils.time_utils import to_time_str, TIME_FORMAT_DAY, now_pd_timestamp


class EmBaseChinaStockFinanceRecorder(TimeSeriesDataRecorder):
    finance_report_type = None
    data_type = 1

    entity_provider = 'joinquant'
    entity_schema = StockDetail
    provider = 'emquantapi'

    def __init__(self, entity_type='stock', exchanges=['sh', 'sz'], entity_ids=None, codes=None, batch_size=10,
                 force_update=False, sleeping_time=5, default_size=2000, real_time=False,
                 fix_duplicate_way='add', start_timestamp=None, end_timestamp=None, close_hour=0,
                 close_minute=0) -> None:
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
        reportdate_list = list({to_time_str(i)[:4] + '-03-31' for i in pd.date_range(start, end)}) + list(
            {to_time_str(i)[:4] + '-06-30' for i in pd.date_range(start, end)}) + list(
            {to_time_str(i)[:4] + '-09-30' for i in pd.date_range(start, end)}) + list(
            {to_time_str(i)[:4] + '-12-31' for i in pd.date_range(start, end)})
        em_code = to_em_entity_id(entity)
        df = pd.DataFrame()
        columns_map = {key:value[0] for key,value in self.get_data_map().items()}
        columns_list =list(columns_map.values())

        for reportdate in reportdate_list:
            # 获取数据
            # 三大财务报表 使用ctr方法读取表名
            if self.data_type < 4:
                data = c.ctr(self.finance_report_type, columns_list,
                             "secucode=" + em_code + ",ReportDate=" + reportdate + ",ReportType=1")
                if data.Data == {}:
                    continue
                data = pd.DataFrame(data.Data['0']).T
                df = df.append(data)
            # 否则用 css方法读取单个指标
            else:
                if 'REPORTDATE' in columns_list:
                    columns_list.remove('REPORTDATE')
                data = c.css(em_code, columns_list,"ReportDate="+reportdate)
                data = pd.DataFrame(data.Data[em_code]).T
                data[len(columns_list)+1] = reportdate
                df = df.append(data)
        # if self.finance_report_type in ['FinanceDerivative','FinancePerShare','FinanceGrowthAbility']:
        if df.empty:
            return None
        if self.data_type > 4:
            columns_list.append('REPORTDATE')
        df.columns = columns_list
        df = df.sort_values("REPORTDATE", ascending=True)
        if pd_is_not_null(df):
            df.reset_index(drop=True, inplace=True)
            df.rename(columns={value:key for key,value in columns_map.items()}, inplace=True)
            df['entity_id'] = entity.id
            df['timestamp'] = pd.to_datetime(df.report_date)
            df['provider'] = 'emquantapi'
            df['code'] = entity.code
            df['report_period'] = df['report_date'].apply(lambda x: get_recent_report_period(x))
            def generate_id(se):
                return "{}_{}".format(se['entity_id'], to_time_str(se['timestamp'], fmt=TIME_FORMAT_DAY))

            df['id'] = df[['entity_id', 'timestamp']].apply(generate_id, axis=1)
            df_to_db(df=df, data_schema=self.data_schema, provider=self.provider, force_update=self.force_update)
        return None

    def get_original_time_field(self):
        return 'ReportDate'
