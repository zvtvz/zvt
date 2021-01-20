# -*- coding: utf-8 -*-
import pandas as pd
from jqdatapy.api import run_query

from zvt.api import portfolio_relate_stock, china_stock_code_to_id
from zvt.contract.api import df_to_db
from zvt.contract.recorder import Recorder, TimeSeriesDataRecorder
from zvt.domain.meta.fund_meta import Fund, FundStock
from zvt.recorders.joinquant.common import to_entity_id, jq_to_report_period
from zvt.utils.pd_utils import pd_is_not_null
from zvt.utils.time_utils import to_time_str, next_date, now_pd_timestamp, is_same_date


class JqChinaFundRecorder(Recorder):
    provider = 'joinquant'
    data_schema = Fund

    def run(self):
        # 按不同类别抓取
        # 编码	基金运作方式
        # 401001	开放式基金
        # 401002	封闭式基金
        # 401003	QDII
        # 401004	FOF
        # 401005	ETF
        # 401006	LOF
        for operate_mode_id in (401001, 401002, 401005):
            year_count = 2
            while True:
                latest = Fund.query_data(filters=[Fund.operate_mode_id == operate_mode_id], order=Fund.timestamp.desc(),
                                         limit=1, return_type='domain')
                start_timestamp = '2000-01-01'
                if latest:
                    start_timestamp = latest[0].timestamp

                end_timestamp = min(next_date(start_timestamp, 365 * year_count), now_pd_timestamp())

                df = run_query(table='finance.FUND_MAIN_INFO',
                               conditions=f'operate_mode_id#=#{operate_mode_id}&start_date#>=#{to_time_str(start_timestamp)}&start_date#<=#{to_time_str(end_timestamp)}',
                               parse_dates=['start_date', 'end_date'],
                               dtype={'main_code': str})
                if not pd_is_not_null(df) or (df['start_date'].max().year < end_timestamp.year):
                    year_count = year_count + 1

                if pd_is_not_null(df):
                    df.rename(columns={'start_date': 'timestamp'}, inplace=True)
                    df['timestamp'] = pd.to_datetime(df['timestamp'])
                    df['list_date'] = df['timestamp']
                    df['end_date'] = pd.to_datetime(df['end_date'])

                    df['code'] = df['main_code']
                    df['entity_id'] = df['code'].apply(lambda x: to_entity_id(entity_type='fund', jq_code=x))
                    df['id'] = df['entity_id']
                    df['entity_type'] = 'fund'
                    df['exchange'] = 'sz'
                    df_to_db(df, data_schema=Fund, provider=self.provider, force_update=self.force_update)
                    self.logger.info(
                        f'persist fund {operate_mode_id} list success {start_timestamp} to {end_timestamp}')

                if is_same_date(end_timestamp, now_pd_timestamp()):
                    break


class JqChinaFundStockRecorder(TimeSeriesDataRecorder):
    entity_provider = 'joinquant'
    entity_schema = Fund

    provider = 'joinquant'
    data_schema = FundStock

    def __init__(self, entity_ids=None, codes=None, day_data=True, batch_size=10,
                 force_update=False, sleeping_time=5, default_size=2000, real_time=False, fix_duplicate_way='add',
                 start_timestamp=None, end_timestamp=None, close_hour=0, close_minute=0) -> None:
        super().__init__('fund', ['sh', 'sz'], entity_ids, codes, day_data, batch_size, force_update, sleeping_time,
                         default_size, real_time, fix_duplicate_way, start_timestamp, end_timestamp, close_hour,
                         close_minute)

    def init_entities(self):
        # 只抓股票型，混合型并且没退市的持仓,
        self.entities = Fund.query_data(
            entity_ids=self.entity_ids,
            codes=self.codes,
            return_type='domain',
            provider=self.entity_provider,
            filters=[Fund.underlying_asset_type.in_(('股票型', '混合型')), Fund.end_date.is_(None)])

    def record(self, entity, start, end, size, timestamps):
        # 忽略退市的
        if entity.end_date:
            return None
        redundant_times = 1
        while redundant_times > 0:
            df = run_query(table='finance.FUND_PORTFOLIO_STOCK',
                           conditions=f'pub_date#>=#{to_time_str(start)}&code#=#{entity.code}',
                           parse_dates=None)
            df = df.dropna()
            if pd_is_not_null(df):
                # data format
                #          id    code period_start  period_end    pub_date  report_type_id report_type  rank  symbol  name      shares    market_cap  proportion
                # 0   8640569  159919   2018-07-01  2018-09-30  2018-10-26          403003        第三季度     1  601318  中国平安  19869239.0  1.361043e+09        7.09
                # 1   8640570  159919   2018-07-01  2018-09-30  2018-10-26          403003        第三季度     2  600519  贵州茅台    921670.0  6.728191e+08        3.50
                # 2   8640571  159919   2018-07-01  2018-09-30  2018-10-26          403003        第三季度     3  600036  招商银行  18918815.0  5.806184e+08        3.02
                # 3   8640572  159919   2018-07-01  2018-09-30  2018-10-26          403003        第三季度     4  601166  兴业银行  22862332.0  3.646542e+08        1.90
                df['timestamp'] = pd.to_datetime(df['pub_date'])

                df.rename(columns={'symbol': 'stock_code', 'name': 'stock_name'}, inplace=True)
                df['proportion'] = df['proportion'] * 0.01

                df = portfolio_relate_stock(df, entity)

                df['stock_id'] = df['stock_code'].apply(lambda x: china_stock_code_to_id(x))
                df['id'] = df[['entity_id', 'stock_id', 'pub_date', 'id']].apply(lambda x: '_'.join(x.astype(str)),
                                                                                 axis=1)
                df['report_date'] = pd.to_datetime(df['period_end'])
                df['report_period'] = df['report_type'].apply(lambda x: jq_to_report_period(x))

                saved = df_to_db(df=df, data_schema=self.data_schema, provider=self.provider,
                                 force_update=self.force_update)

                # 取不到非重复的数据
                if saved == 0:
                    return None

                # self.logger.info(df.tail())
                self.logger.info(
                    f"persist fund {entity.code}({entity.name}) portfolio success {df.iloc[-1]['pub_date']}")
                latest = df['timestamp'].max()

                # 取到了最近两年的数据，再请求一次,确保取完最新的数据
                if latest.year >= now_pd_timestamp().year - 1:
                    redundant_times = redundant_times - 1
                start = latest
            else:
                return None

        return None


if __name__ == '__main__':
    # JqChinaFundRecorder().run()
    JqChinaFundStockRecorder(codes=['000053']).run()
# the __all__ is generated
__all__ = ['JqChinaFundRecorder', 'JqChinaFundStockRecorder']
