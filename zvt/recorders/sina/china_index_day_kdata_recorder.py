# -*- coding: utf-8 -*-

import time

import pandas as pd
import requests

from zvt.api.quote import generate_kdata_id
from zvt.contract import IntervalLevel
from zvt.contract.recorder import FixedCycleDataRecorder
from zvt.domain import Index, Index1dKdata
from zvt.utils.time_utils import get_year_quarters, is_same_date


class ChinaIndexDayKdataRecorder(FixedCycleDataRecorder):
    entity_provider = 'exchange'
    entity_schema = Index

    provider = 'sina'
    data_schema = Index1dKdata
    url = 'http://vip.stock.finance.sina.com.cn/corp/go.php/vMS_MarketHistory/stockid/{}/type/S.phtml?year={}&jidu={}'

    def __init__(self, entity_type='index', exchanges=['cn'], entity_ids=None, codes=None, day_data=False,
                 batch_size=10,
                 force_update=False, sleeping_time=10, default_size=2000, real_time=False, fix_duplicate_way='add',
                 start_timestamp=None, end_timestamp=None,
                 level=IntervalLevel.LEVEL_1DAY, kdata_use_begin_time=False, close_hour=0, close_minute=0,
                 one_day_trading_minutes=24 * 60) -> None:
        super().__init__(entity_type, exchanges, entity_ids, codes, day_data, batch_size, force_update, sleeping_time,
                         default_size, real_time, fix_duplicate_way, start_timestamp, end_timestamp, close_hour,
                         close_minute, level, kdata_use_begin_time, one_day_trading_minutes)

    def get_data_map(self):
        return {}

    def generate_domain_id(self, entity, original_data):
        return generate_kdata_id(entity.id, timestamp=original_data['timestamp'], level=self.level)

    def record(self, entity, start, end, size, timestamps):
        the_quarters = get_year_quarters(start)
        if not is_same_date(entity.timestamp, start) and len(the_quarters) > 1:
            the_quarters = the_quarters[1:]

        param = {
            'security_item': entity,
            'quarters': the_quarters,
            'level': self.level.value
        }

        security_item = param['security_item']
        quarters = param['quarters']
        level = param['level']

        result_df = pd.DataFrame()
        for year, quarter in quarters:
            query_url = self.url.format(security_item.code, year, quarter)
            response = requests.get(query_url)
            response.encoding = 'gbk'

            try:
                dfs = pd.read_html(response.text)
            except ValueError as error:
                self.logger.error(f'skip ({year}-{quarter:02d}){security_item.code}{security_item.name}({error})')
                time.sleep(10.0)
                continue

            if len(dfs) < 5:
                time.sleep(10.0)
                continue

            df = dfs[4].copy()
            df = df.iloc[1:]
            df.columns = ['timestamp', 'open', 'high', 'close', 'low', 'volume', 'turnover']
            df['name'] = security_item.name
            df['level'] = level
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df['provider'] = 'sina'

            result_df = pd.concat([result_df, df])

            self.logger.info(f'({security_item.code}{security_item.name})({year}-{quarter:02d})')
            time.sleep(10.0)

        result_df = result_df.sort_values(by='timestamp')

        return result_df.to_dict(orient='records')


__all__ = ['ChinaIndexDayKdataRecorder']

if __name__ == '__main__':
    ChinaIndexDayKdataRecorder().run()
