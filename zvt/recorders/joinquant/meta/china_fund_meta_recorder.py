# -*- coding: utf-8 -*-
import pandas as pd
from jqdatapy.api import run_query

from zvt.contract.api import df_to_db
from zvt.contract.recorder import Recorder
from zvt.domain.meta.fund import Fund
from zvt.recorders.joinquant.common import to_entity_id
from zvt.utils.pd_utils import pd_is_not_null
from zvt.utils.time_utils import to_time_str, next_date, now_pd_timestamp, is_same_date


class JqChinaFundRecorder(Recorder):
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


if __name__ == '__main__':
    JqChinaFundRecorder().run()
# the __all__ is generated
__all__ = ['JqChinaFundRecorder']