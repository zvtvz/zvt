# -*- coding: utf-8 -*-

import pandas as pd
from sqlalchemy import create_engine

from zvt.contract.api import df_to_db
from zvt.contract.recorder import TimeSeriesDataRecorder
from zvt.utils.time_utils import now_pd_timestamp, now_time_str, to_time_str
from zvt import zvt_env
from zvt.domain import Stock, StockValuation, Etf
from zvt.recorders.tonglian.common import to_jq_entity_id


class TlChinaStockValuationRecorder(TimeSeriesDataRecorder):
    entity_provider = 'tonglian'
    entity_schema = Stock

    # 数据来自jq
    provider = 'tonglian'

    data_schema = StockValuation

    def __init__(self, entity_type='stock', exchanges=None, entity_ids=None, codes=None, batch_size=10,
                 force_update=False, sleeping_time=5, default_size=2000, real_time=False, fix_duplicate_way='add',
                 start_timestamp=None, end_timestamp=None, close_hour=0, close_minute=0) -> None:
        super().__init__(entity_type, exchanges, entity_ids, codes, batch_size, force_update, sleeping_time,
                         default_size, real_time, fix_duplicate_way, start_timestamp, end_timestamp, close_hour,
                         close_minute)
        self.tonglian_conn = create_engine(
            f"mysql://{zvt_env['tl_username']}:{zvt_env['tl_password']}@{zvt_env['tl_server_address']}:"
            f"{zvt_env['tl_server_port']}/{zvt_env['tl_db_name']}?charset=utf8mb4", pool_recycle=3600,
            echo=False).connect()

    def on_finish(self):
        super().on_finish()
        self.tonglian_conn.close()

    def record(self, entity, start, end, size, timestamps):

        sql_valuation = 'SELECT a.TRADE_DATE,a.TICKER_SYMBOL,a.PE,a.PB,a.PCF,a.PS FROM equ_factor_VS WHERE TRADE_DATE>=%s AND TRADE_DATE<=%s AND TICKER_SYMBOL=%s'

        df = pd.read_sql(sql_valuation, self.tonglian_conn,
                         params=(to_time_str(start, fmt="YYYYMMDD"), now_time_str(fmt="YYYYMMDD"),entity.code))


        df = pd.read_sql(sql_valuation, self.tonglian_conn,
                         params=(to_time_str(start, fmt="YYYYMMDD").strip('-'), now_time_str(fmt="YYYYMMDD"),"000006"))
        df = df.rename({'TRADE_DATE': 'day',
                        'TICKER_SYMBOL': 'code',
                        'PE': 'pe',
                        'PB': 'pb',
                        'PS': 'ps',
                        'PCF': 'pcf'},
                       axis='columns')


        df['entity_id'] = entity.id
        df['timestamp'] = pd.to_datetime(df['day'])
        df['name'] = entity.name
        df['id'] = df['timestamp'].apply(lambda x: "{}_{}".format(entity.id, to_time_str(x)))

        df['market_cap'] = df['market_cap'] * 100000000  # 总市值
        df['circulating_market_cap'] = df['circulating_market_cap'] * 100000000  # 流通市值
        df['capitalization'] = df['capitalization'] * 10000   #总股本
        df['circulating_cap'] = df['circulating_cap'] * 10000  #流通股
        df['turnover_ratio'] = df['turnover_ratio'] * 0.01    #换手率
        df_to_db(df=df, data_schema=self.data_schema, provider=self.provider, force_update=self.force_update)

        return None


__all__ = ['TlChinaStockValuationRecorder']

if __name__ == '__main__':
    # 上证50
    df = Etf.get_stocks(code='510050')

    stocks = df.stock_id.tolist()
    print(stocks)
    print(len(stocks))

    TlChinaStockValuationRecorder(entity_ids=stocks, force_update=True).run()
