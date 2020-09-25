# -*- coding: utf-8 -*-
import pandas as pd
from EmQuantAPI import *
from zvt.contract.api import df_to_db
from zvt.contract.recorder import TimeSeriesDataRecorder, FixedCycleDataRecorder
from zvt.utils.time_utils import now_pd_timestamp, now_time_str, to_time_str
from zvt.domain import IndexValuation,Index
from zvt.contract import IntervalLevel
from zvt.api import get_kdata, AdjustType
code_map_choice = {
    '000001': 'SH', '000002': 'SH', '000003': 'SH',
    '000010': 'SH', '000016': 'SH', '000017': 'SH',
    '000300': 'SH', '000688': 'SH', '000903': 'SH',
    '000905': 'SH', '399001': 'SZ', '399004': 'SZ',
    '399005': 'SZ', '399006': 'SZ', '399008': 'SZ',
    '399100': 'SZ', '399101': 'SZ', '399102': 'SZ',
    '399106': 'SZ', '399107': 'SZ', '399108': 'SZ',
    '399293': 'SZ', '399314': 'SZ', '399315': 'SZ',
    '399316': 'SZ', '399344': 'SZ', '399372': 'SZ',
    '399373': 'SZ', '399374': 'SZ', '399375': 'SZ',
    '399376': 'SZ', '399377': 'SZ', '800000': 'EI',
    '800001': 'EI', '801001': 'SWI', '801002': 'SWI',
    '801003': 'SWI', '801005': 'SWI', '801300': 'SWI',
    '899001': 'CSI', '899002': 'CSI', '910073': 'EI',
    '910074': 'EI', '910075': 'EI', '910076': 'EI', 'CN2293': 'SZ',
}


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
        # loginResult = c.start("ForceLogin=1", '')
        # if (loginResult.ErrorCode != 0):
        #     print("login in fail")
        #     exit()


    def on_finish(self):
        # 退出
        loginresult = c.stop()
        if (loginresult.ErrorCode != 0):
            print("login in fail")
            exit()

    def record(self, entity, start, end, size, timestamps):
        if not end:
            end = to_time_str(now_pd_timestamp())
        if size >= 2000:
            from datetime import timedelta
            end = to_time_str(start+timedelta(days=1000))
        start = to_time_str(start)
        em_code = entity.code+'.'+code_map_choice[entity.code]
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
        df = c.csd(em_code, [i for i in columns_list.keys()], start,end,"ispandas=1")
        df = df.rename(columns = columns_list)

        df['entity_id'] = entity.id[:15]
        df['timestamp'] = pd.to_datetime(df['DATES'])
        df['code'] = entity.code
        df['name'] = entity.name
        df['id'] = df.apply(lambda x: "{}_{}".format(x.entity_id, to_time_str(x.timestamp)),axis=1)

        df_to_db(df=df, data_schema=self.data_schema, provider=self.provider, force_update=self.force_update)
        return None


__all__ = ['EmChinaStockValuationRecorder']
