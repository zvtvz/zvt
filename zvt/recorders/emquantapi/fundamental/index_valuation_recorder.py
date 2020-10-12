# -*- coding: utf-8 -*-
import pandas as pd
from EmQuantAPI import *
from zvt.contract.api import df_to_db
from zvt.contract.recorder import TimeSeriesDataRecorder, FixedCycleDataRecorder
from zvt.utils.time_utils import now_pd_timestamp, now_time_str, to_time_str
from zvt.domain import IndexValuation,Index

class EmChinaStockValuationRecorder(TimeSeriesDataRecorder):
    entity_provider = 'emquantapi'
    entity_schema = Index

    # 数据来自choice
    provider = 'emquantapi'

    data_schema = IndexValuation

    def __init__(self, entity_type='index', exchanges=None, entity_ids=None, codes=None, batch_size=10,
                 force_update=False, sleeping_time=5, default_size=2000, real_time=False, fix_duplicate_way='add',
                 start_timestamp=None, end_timestamp=None, close_hour=0, close_minute=0) -> None:
        super().__init__(entity_type, exchanges, entity_ids, codes, batch_size, force_update, sleeping_time,
                         default_size, real_time, fix_duplicate_way, start_timestamp, end_timestamp, close_hour,
                         close_minute)

        # 调用登录函数（激活后使用，不需要用户名密码）
        loginResult = c.start("ForceLogin=1", '')
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
        if (pd.to_datetime(end) - start).days >=800:
            from datetime import timedelta
            end = to_time_str(start+timedelta(days=800))
        start = to_time_str(start)
        exchange = 'SH' if 'sh' in entity.id else  'SZ'
        em_code = entity.code+'.'+exchange
        if em_code == '000022.SH':
            return None
        columns_list = {
            'MV': 'market_cap', #总市值
            'LIQMV': 'circulating_market_cap', #流通市值
            'TURN': 'turnover_ratio', #换手率
            'PELYR': 'pe', # 静态pe
            'PETTM': 'pe_ttm', # 动态pe
            'PBLYR': 'pb', # 市净率PB(最新年报)
            'PBMRQ': 'pb_mrq', # 市净率PB(MRQ)
            'PSTTM': 'ps_ttm', #市销率PS(TTM)
            'PCFTTM': 'pcf_ttm', #市现率PCF(最新年报，经营性现金流)
            'DIVIDENDYIELD': 'div_yield', #股息率
        }
        df = c.csd(em_code, [i for i in columns_list.keys()], start,end,"ispandas=1,DelType=2")
        if not isinstance(df,pd.DataFrame):
            return None
        # 该方法会获取到未来数据,总市值为Nan时删除该条
        df = df.dropna(subset=['MV'])
        if df.empty:
            return None
        df = df.rename(columns = columns_list)

        df['entity_id'] = entity.id[:15]
        df['timestamp'] = pd.to_datetime(df['DATES'])
        df['code'] = entity.code
        df['name'] = entity.name
        df['id'] = df.apply(lambda x: "{}_{}".format(x.entity_id, to_time_str(x.timestamp)),axis=1)

        df_to_db(df=df, data_schema=self.data_schema, provider=self.provider, force_update=self.force_update)
        return None


__all__ = ['EmChinaStockValuationRecorder']
