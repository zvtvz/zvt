# -*- coding: utf-8 -*-

from EmQuantAPI import *
from zvt.recorders.emquantapi.common import mainCallback, to_em_entity_id
import pandas as pd
from jqdatasdk import auth, get_query_count, get_industries, get_industry_stocks, finance, query

from zvt.contract.api import df_to_db
from zvt.contract.recorder import Recorder, TimeSeriesDataRecorder
from zvt.recorders.joinquant.common import to_entity_id
from zvt.utils.pd_utils import pd_is_not_null
from zvt.utils.time_utils import now_pd_timestamp, to_time_str, TIME_FORMAT_DAY
from zvt.domain import BlockStock, Block,Block1dKdata,BlockMoneyFlow


class EmChinaBlockRecorder(Recorder):
    """
    choice板块数据
    """
    provider = 'emquantapi'
    data_schema = Block

    category_map = {
        "sw_l1": "申万一级行业",
        "sw_l2": "申万二级行业",
        "sw_l3": "申万三级行业",
        "zjw": "证监会行业",
    }

    def __init__(self, batch_size=10, force_update=True, sleeping_time=10) -> None:
        super().__init__(batch_size, force_update, sleeping_time)

        # 调用登录函数（激活后使用，不需要用户名密码）
        loginResult = c.start("ForceLogin=1", '', mainCallback)
        if (loginResult.ErrorCode != 0):
            print("login in fail")
            exit()


    def run(self):
        # get stock blocks from sina
        for category, name_ch in self.category_map.items():
            df = get_industries(name=category, date=None)
            df['code'] = df.index
            df['exchange'] = category.replace("_","")
            df['list_date'] = df['start_date']
            df['timestamp'] = df['list_date']
            df['entity_type'] = 'block'
            df['category'] = "industry"
            df['id'] = df['entity_id'] = df.apply(lambda x: "block_" + x.exchange + "_" + x.code, axis=1)
            df_to_db(data_schema=self.data_schema, df=df, provider=self.provider,
                     force_update=True)
            self.logger.info(f"完成choice数据行业数据保存:{name_ch}")


class EmChinaBlockStockRecorder(TimeSeriesDataRecorder):
    entity_provider = 'joinquant'
    entity_schema = Block

    provider = 'emquantapi'
    data_schema = BlockStock

    def __init__(self, entity_type='block', exchanges=None, entity_ids=None, codes=None, batch_size=10,
                 force_update=True, sleeping_time=5, default_size=2000, real_time=False, fix_duplicate_way='add',
                 start_timestamp=None, end_timestamp=None, close_hour=0, close_minute=0) -> None:
        super().__init__(entity_type, exchanges, entity_ids, codes, batch_size, force_update, sleeping_time,
                         default_size, real_time, fix_duplicate_way, start_timestamp, end_timestamp, close_hour,
                         close_minute)
        # 调用登录函数（激活后使用，不需要用户名密码）
        loginResult = c.start("ForceLogin=1", '', mainCallback)
        if (loginResult.ErrorCode != 0):
            print("login in fail")
            exit()

    def record(self, entity, start, end, size, timestamps):

        industry_stocks = get_industry_stocks(entity.code,date=now_pd_timestamp())
        if len(industry_stocks)==0:
            return None
        df = pd.DataFrame({"stock":industry_stocks})
        df["stock_id"] = df.stock.apply(lambda x:to_entity_id(x,"stock"))
        df["stock_code"] = df.stock_id.str.split("_", expand=True)[2]

        df["code"] = entity.code
        df["name"] = entity.name
        df["exchange"] = entity.exchange
        df["timestamp"] = now_pd_timestamp()
        df["entity_id"] = entity.id
        df["entity_type"] = "block"
        df["id"] = df.apply(lambda x:x.entity_id+"_"+x.stock_id,axis=1)
        if df.empty:
            return None
        df_to_db(data_schema=self.data_schema, df=df, provider=self.provider,
                 force_update=True)

        self.logger.info('finish recording BlockStock:{},{}'.format(entity.category, entity.name))


class JqChinaBlockKdataRecorder(TimeSeriesDataRecorder):
    entity_provider = 'joinquant'
    entity_schema = Block

    provider = 'emquantapi'
    data_schema = Block1dKdata

    def __init__(self, entity_type='block', exchanges=None, entity_ids=None, codes=None, batch_size=10,
                 force_update=True, sleeping_time=5, default_size=2000, real_time=False, fix_duplicate_way='add',
                 start_timestamp=None, end_timestamp=None, close_hour=0, close_minute=0) -> None:
        super().__init__(entity_type, exchanges, entity_ids, codes, batch_size, force_update, sleeping_time,
                         default_size, real_time, fix_duplicate_way, start_timestamp, end_timestamp, close_hour,
                         close_minute)

        # 调用登录函数（激活后使用，不需要用户名密码）
        loginResult = c.start("ForceLogin=1", '', mainCallback)
        if (loginResult.ErrorCode != 0):
            print("login in fail")
            exit()

    def record(self, entity, start, end, size, timestamps):
        if entity.exchange == "swl1":
            return None
        if not end:
            if (now_pd_timestamp() - start).days > 365:
                from datetime import timedelta
                end = to_time_str(start + timedelta(days=365))
            else:
                end= to_time_str(now_pd_timestamp())
        start = to_time_str(start)
        df = c.csd(f"{entity.code}.SWI", "OPEN,CLOSE,HIGH,LOW,VOLUME,AMOUNT", start, end,
                     "period=1,adjustflag=1,curtype=1,order=1,ispandas=1")
        if type(df) != pd.DataFrame:
            return None
        df.rename(columns={
                'DATES': 'timestamp',
                'OPEN': 'open',
                'CLOSE': 'close',
                'HIGH': 'high',
                'LOW': 'low',
                'VOLUME': 'volume',
                'AMOUNT': 'turnover',
        }, inplace=True)

        if pd_is_not_null(df):
            df['name'] = entity.name


            df['entity_id'] = entity.id
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df['provider'] = 'joinquant'
            df['level'] = '1d'
            df['code'] = entity.code


            def generate_kdata_id(se):
                return "{}_{}".format(se['entity_id'], to_time_str(se['timestamp'], fmt=TIME_FORMAT_DAY))

            df['id'] = df[['entity_id', 'timestamp']].apply(generate_kdata_id, axis=1)

            df_to_db(df=df, data_schema=self.data_schema, provider=self.provider, force_update=self.force_update)

        return None

class JqChinaBlockMoneyFlowRecorder(TimeSeriesDataRecorder):
    # entity_provider = 'joinquant'
    # entity_schema = Block

    provider = 'emquantapi'
    data_schema = BlockMoneyFlow

    def __init__(self, entity_type='block', exchanges=None, entity_ids=None, codes=None, batch_size=10,
                 force_update=True, sleeping_time=5, default_size=2000, real_time=False, fix_duplicate_way='add',
                 start_timestamp=None, end_timestamp=None, close_hour=0, close_minute=0) -> None:
        super().__init__(entity_type, exchanges, entity_ids, codes, batch_size, force_update, sleeping_time,
                         default_size, real_time, fix_duplicate_way, start_timestamp, end_timestamp, close_hour,
                         close_minute)

        # 调用登录函数（激活后使用，不需要用户名密码）
        loginResult = c.start("ForceLogin=1", '', mainCallback)
        if (loginResult.ErrorCode != 0):
            print("login in fail")
            exit()

    def record(self, entity, start, end, size, timestamps):
        if "swl1" not in entity.id:
            return None
        start = to_time_str(start)
        df = finance.run_query(
            query(finance.SW1_DAILY_PRICE).filter(
                finance.SW1_DAILY_PRICE.code==entity.code).filter(
                finance.SW1_DAILY_PRICE.date>=start).limit(size))
        if pd_is_not_null(df):
            df['name'] = entity.name
            df.rename(columns={'money': 'turnover', 'date': 'timestamp'}, inplace=True)

            df['entity_id'] = entity.id
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df['provider'] = 'joinquant'
            df['level'] = '1d'
            df['code'] = entity.code


            def generate_kdata_id(se):
                return "{}_{}".format(se['entity_id'], to_time_str(se['timestamp'], fmt=TIME_FORMAT_DAY))

            df['id'] = df[['entity_id', 'timestamp']].apply(generate_kdata_id, axis=1)

            df_to_db(df=df, data_schema=self.data_schema, provider=self.provider, force_update=self.force_update)

        return None

__all__ = ['EmChinaBlockRecorder', 'EmChinaBlockStockRecorder']

if __name__ == '__main__':
    # init_log('sina_china_stock_category.log')

    recorder = EmChinaBlockStockRecorder()
    recorder.run()
