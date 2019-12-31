# -*- coding: utf-8 -*-
import pandas as pd
from jqdatasdk import auth, get_all_securities, logout, query, finance

from zvdata.api import df_to_db, get_entity_exchange, get_entity_code
from zvdata.recorder import Recorder, TimeSeriesDataRecorder
from zvdata.utils.time_utils import now_pd_timestamp
from zvt import zvt_env
from zvt.domain import StockIndex
from zvt.domain.meta.stock_meta import Index
from zvt.recorders.joinquant import to_entity_id


class ChinaStockEtfListRecorder(Recorder):
    provider = 'joinquant'
    data_schema = StockIndex

    def __init__(self, batch_size=10, force_update=False, sleeping_time=10) -> None:
        super().__init__(batch_size, force_update, sleeping_time)

        auth(zvt_env['jq_username'], zvt_env['jq_password'])

    def run(self):
        df = get_all_securities(['etf'])
        #             display_name      name start_date   end_date type
        # 159001.XSHE          保证金       BZJ 2014-10-20 2200-01-01  etf
        # 159003.XSHE         招商快线      ZSKX 2014-10-20 2200-01-01  etf
        # 159005.XSHE         添富快钱      TFKQ 2015-01-13 2200-01-01  etf
        # 159901.XSHE      深100ETF   S100ETF 2006-04-24 2200-01-01  etf
        df.index.name = 'entity_id'
        df = df.reset_index()

        # 上市日期
        df.rename(columns={'start_date': 'timestamp'}, inplace=True)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        # 转为标准的zvt entity格式
        df['entity_id'] = df['entity_id'].apply(lambda x: to_entity_id(entity_type='index', jq_code=x))
        df['id'] = df['entity_id']
        df['entity_type'] = 'index'
        df['exchange'] = df['entity_id'].apply(lambda x: get_entity_exchange(x))
        df['code'] = df['entity_id'].apply(lambda x: get_entity_code(x))
        df['name'] = df['display_name']
        df['category'] = 'etf'
        df['is_delisted'] = pd.to_datetime(df['end_date']) < now_pd_timestamp()

        df_to_db(df, data_schema=Index, provider=self.provider)


class ChinaStockEtfPortfolioRecorder(TimeSeriesDataRecorder):
    entity_provider = 'joinquant'
    entity_schema = Index

    # 数据来自jq
    provider = 'joinquant'

    data_schema = StockIndex

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
        q = query(finance.FUND_PORTFOLIO_STOCK).filter(finance.FUND_PORTFOLIO_STOCK.pub_date >= start).filter(
            finance.FUND_PORTFOLIO_STOCK.code == entity.code)
        df = finance.run_query(q)
        print(df)

        df['entity_id'] = entity.id
        df['timestamp'] = pd.to_datetime(df['day'])
        df['code'] = entity.code
        df['name'] = entity.name
        df['id'] = df['timestamp'].apply(lambda x: "{}_{}".format(entity.id, to_time_str(x)))
        df = df.rename({'pe_ratio_lyr': 'pe',
                        'pe_ratio': 'pe_ttm',
                        'pb_ratio': 'pb',
                        'ps_ratio': 'ps',
                        'pcf_ratio': 'pcf'},
                       axis='columns')

        df['market_cap'] = df['market_cap'] * 100000000
        df['circulating_cap'] = df['circulating_cap'] * 100000000
        df['capitalization'] = df['capitalization'] * 10000
        df['circulating_cap'] = df['circulating_cap'] * 10000
        df_to_db(df=df, data_schema=self.data_schema, provider=self.provider, force_update=self.force_update)

        return None


if __name__ == '__main__':
    recorder = ChinaStockEtfListRecorder()
    recorder.run()
