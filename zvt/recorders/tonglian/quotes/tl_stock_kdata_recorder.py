# -*- coding: utf-8 -*-
import argparse

import pandas as pd
from sqlalchemy import create_engine

from zvt import init_log, zvt_env
from zvt.api import get_kdata, AdjustType, china_stock_code_to_id
from zvt.api.quote import generate_kdata_id, get_kdata_schema
from zvt.contract import IntervalLevel
from zvt.contract.api import df_to_db
from zvt.contract.recorder import FixedCycleDataRecorder
from zvt.recorders.tonglian.common import to_jq_trading_level, to_jq_entity_id
from zvt.domain import Stock, StockKdataCommon, Stock1dHfqKdata
from zvt.utils.pd_utils import pd_is_not_null
from zvt.utils.time_utils import to_time_str, now_pd_timestamp, TIME_FORMAT_DAY, TIME_FORMAT_ISO8601


class TlChinaStockKdataRecorder(FixedCycleDataRecorder):
    entity_provider = 'tonglian'
    entity_schema = Stock

    # 数据来自jq
    provider = 'tonglian'

    # 只是为了把recorder注册到data_schema
    data_schema = StockKdataCommon

    def __init__(self,
                 exchanges=['sh', 'sz'],
                 entity_ids=None,
                 codes=None,
                 batch_size=10,
                 force_update=True,
                 sleeping_time=0,
                 default_size=2000,
                 real_time=False,
                 fix_duplicate_way='ignore',
                 start_timestamp=None,
                 end_timestamp=None,
                 level=IntervalLevel.LEVEL_1WEEK,
                 kdata_use_begin_time=False,
                 close_hour=15,
                 close_minute=0,
                 one_day_trading_minutes=4 * 60,
                 adjust_type=AdjustType.qfq) -> None:
        level = IntervalLevel(level)
        adjust_type = AdjustType(adjust_type)
        self.data_schema = get_kdata_schema(entity_type='stock', level=level, adjust_type=adjust_type)
        self.tl_trading_level = to_jq_trading_level(level)
        if self.tl_trading_level != "1d":
            self.logger.info('通联数据目前仅支持日K线，level入参仅支持：1d，实际level入参为'.format(self.tl_trading_level))
            raise Exception
        super().__init__('stock', exchanges, entity_ids, codes, batch_size, force_update, sleeping_time,
                         default_size, real_time, fix_duplicate_way, start_timestamp, end_timestamp, close_hour,
                         close_minute, level, kdata_use_begin_time, one_day_trading_minutes)
        self.adjust_type = adjust_type

        self.tonglian_conn = create_engine(
            f"mysql://{zvt_env['tl_username']}:{zvt_env['tl_password']}@{zvt_env['tl_server_address']}:"
            f"{zvt_env['tl_server_port']}/{zvt_env['tl_db_name']}?charset=utf8mb4", pool_recycle=3600, echo=False).connect()


    def on_finish(self):
        super().on_finish()
        self.tonglian_conn.close()

    def record(self, entity, start, end, size, timestamps):
        now_date = to_time_str(now_pd_timestamp())
        sql_bars = 'select a.TRADE_DATE,a.TICKER_SYMBOL,b.SEC_SHORT_NAME,a.PRE_CLOSE_PRICE_1,' \
                   ' a.OPEN_PRICE_1,a.CLOSE_PRICE_1,a.HIGHEST_PRICE_1,a.LOWEST_PRICE_1,c.TURNOVER_VOL,' \
                   'c.TURNOVER_VALUE,c.DEAL_AMOUNT,c.CHG_PCT,c.NEG_MARKET_VALUE,c.MARKET_VALUE, c.TURNOVER_RATE ' \
                   'from mkt_equd_adj a,md_security b,mkt_equd c ' \
                   'where a.SECURITY_ID=b.SECURITY_ID ' \
                   'and a.TICKER_SYMBOL=c.TICKER_SYMBOL ' \
                   'and a.TRADE_DATE=c.TRADE_DATE ' \
                   'and a.TRADE_DATE>=%s ' \
                   'and a.TRADE_DATE<=%s and a.HIGHEST_PRICE_1!=0 and a.TICKER_SYMBOL=%s'

        if not self.end_timestamp:
            prev_trade_date = self.get_prev_trade_date(self.tonglian_conn, now_date)
            df = pd.read_sql(sql_bars, self.tonglian_conn, params=(prev_trade_date, now_date,entity.code))

        else:
            end_timestamp = to_time_str(self.end_timestamp)
            prev_end_timestamp = self.get_prev_trade_date(self.tonglian_conn, end_timestamp)
            df = pd.read_sql(sql_bars, self.tonglian_conn, params=(prev_end_timestamp, end_timestamp,entity.code))
        if pd_is_not_null(df):
            df.rename(columns={'TICKER_SYMBOL': 'code',
                               'TRADE_DATE': 'timestamp',
                               'OPEN_PRICE_1': 'open',    #开盘价
                               'CLOSE_PRICE_1': 'close',   #收盘价
                               'HIGHEST_PRICE_1': 'high', #最高价
                               'LOWEST_PRICE_1': 'low',  #最低价
                               'TURNOVER_VOL': 'volume',    #成交量
                               'TURNOVER_VALUE': 'money',    #成交额
                               'SEC_SHORT_NAME': 'name',    #证券名称
                               }, inplace=True)
            df = df[['timestamp', 'code','name','open', 'close', 'low', 'high', 'volume', 'money']]
            df['entity_id'] = entity.id
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df['provider'] = 'tonglian'
            df['level'] = self.level.value
            def generate_kdata_id(se):
                if self.level >= IntervalLevel.LEVEL_1DAY:
                    return "{}_{}".format(se['entity_id'], to_time_str(se['timestamp'], fmt=TIME_FORMAT_DAY))
                else:
                    return "{}_{}".format(se['entity_id'], to_time_str(se['timestamp'], fmt=TIME_FORMAT_ISO8601))
            df['id'] = df[['entity_id', 'timestamp']].apply(generate_kdata_id, axis=1)
            df_to_db(df=df, data_schema=self.data_schema, provider=self.provider, force_update=self.force_update)

        return None

    def get_prev_trade_date(self,conn, date):
        """
        获取date往前或往后日期单位
        :param conn:
        :return:
        """
        # XSHG上海证券交易所
        # XSHE深圳证券交易所
        sql_shift_trade_day = "select PREV_TRADE_DATE from md_trade_cal " \
                              "where CALENDAR_DATE=%s " \
                              "AND EXCHANGE_CD IN ('XSHG')"
        return to_time_str(pd.read_sql(sql_shift_trade_day, conn, params=(date,)).PREV_TRADE_DATE[0])

    def is_trade_day(self, conn):
        """
        判断该日期是否为交易日
        :param conn:
        :return:
        """
        pass

    def get_trade_dates(self, conn, start, end, order="ESC"):
        """
            获取start到end(包括start、end)之间的交易日期列表
            start所表示的日期在end之前
        :param end:
        :param order:
        :return:
        """
        pass


__all__ = ['TlChinaStockKdataRecorder']

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--level', help='trading level', default='1d', choices=[item.value for item in IntervalLevel])
    parser.add_argument('--codes', help='codes', default=['600118'], nargs='+')

    args = parser.parse_args()

    level = IntervalLevel(args.level)
    codes = args.codes

    init_log('tl_china_stock_{}_kdata.log'.format(args.level))
    TlChinaStockKdataRecorder(level=level, sleeping_time=0, codes=codes, real_time=False,
                              adjust_type=AdjustType.hfq).run()

    print(get_kdata(entity_id=china_stock_code_to_id(args.codes[0]), limit=10, order=Stock1dHfqKdata.timestamp.desc(),adjust_type=AdjustType.hfq))

