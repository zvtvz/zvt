# -*- coding: utf-8 -*-

import demjson
import pandas as pd
import requests

from zvt.contract import IntervalLevel
from zvt.contract.recorder import FixedCycleDataRecorder
from zvt.utils.time_utils import to_time_str
from zvt import init_log
from zvt.api.quote import generate_kdata_id
from zvt.api import get_kdata
from zvt.domain import Etf, Index, Etf1dKdata
from zvt.recorders.consts import EASTMONEY_ETF_NET_VALUE_HEADER


class ChinaETFDayKdataRecorder(FixedCycleDataRecorder):
    entity_provider = 'exchange'
    entity_schema = Etf

    provider = 'sina'
    data_schema = Etf1dKdata
    url = 'http://money.finance.sina.com.cn/quotes_service/api/json_v2.php/CN_MarketData.getKLineData?' \
          'symbol={}{}&scale=240&&datalen={}&ma=no'

    def __init__(self, entity_type='etf', exchanges=['sh', 'sz'], entity_ids=None, codes=None, day_data=False, batch_size=10,
                 force_update=False, sleeping_time=10, default_size=2000, real_time=True, fix_duplicate_way='add',
                 start_timestamp=None, end_timestamp=None,
                 level=IntervalLevel.LEVEL_1DAY, kdata_use_begin_time=False, close_hour=0, close_minute=0,
                 one_day_trading_minutes=24 * 60) -> None:
        super().__init__(entity_type, exchanges, entity_ids, codes, day_data, batch_size, force_update, sleeping_time,
                         default_size, real_time, fix_duplicate_way, start_timestamp, end_timestamp, close_hour,
                         close_minute, level, kdata_use_begin_time, one_day_trading_minutes)

    def get_data_map(self):
        return {}

    def generate_domain_id(self, entity, original_data):
        return generate_kdata_id(entity_id=entity.id, timestamp=original_data['timestamp'], level=self.level)

    def on_finish_entity(self, entity):
        kdatas = get_kdata(entity_id=entity.id, level=IntervalLevel.LEVEL_1DAY.value,
                           order=Etf1dKdata.timestamp.asc(),
                           return_type='domain', session=self.session,
                           filters=[Etf1dKdata.cumulative_net_value.is_(None)])

        if kdatas and len(kdatas) > 0:
            start = kdatas[0].timestamp
            end = kdatas[-1].timestamp

            # 从东方财富获取基金累计净值
            df = self.fetch_cumulative_net_value(entity, start, end)

            if df is not None and not df.empty:
                for kdata in kdatas:
                    if kdata.timestamp in df.index:
                        kdata.cumulative_net_value = df.loc[kdata.timestamp, 'LJJZ']
                        kdata.change_pct = df.loc[kdata.timestamp, 'JZZZL']
                self.session.commit()
                self.logger.info(f'{entity.code} - {entity.name}累计净值更新完成...')

    def fetch_cumulative_net_value(self, security_item, start, end) -> pd.DataFrame:
        query_url = 'http://api.fund.eastmoney.com/f10/lsjz?' \
                    'fundCode={}&pageIndex={}&pageSize=200&startDate={}&endDate={}'

        page = 1
        df = pd.DataFrame()
        while True:
            url = query_url.format(security_item.code, page, to_time_str(start), to_time_str(end))

            response = requests.get(url, headers=EASTMONEY_ETF_NET_VALUE_HEADER)
            response_json = demjson.decode(response.text)
            response_df = pd.DataFrame(response_json['Data']['LSJZList'])

            # 最后一页
            if response_df.empty:
                break

            response_df['FSRQ'] = pd.to_datetime(response_df['FSRQ'])
            response_df['JZZZL'] = pd.to_numeric(response_df['JZZZL'], errors='coerce')
            response_df['LJJZ'] = pd.to_numeric(response_df['LJJZ'], errors='coerce')
            response_df = response_df.fillna(0)
            response_df.set_index('FSRQ', inplace=True, drop=True)

            df = pd.concat([df, response_df])
            page += 1

            self.sleep()

        return df

    def record(self, entity, start, end, size, timestamps):
        # 此 url 不支持分页，如果超过我们想取的条数，则只能取最大条数
        if start is None or size > self.default_size:
            size = 8000

        param = {
            'security_item': entity,
            'level': self.level.value,
            'size': size
        }

        security_item = param['security_item']
        size = param['size']

        url = ChinaETFDayKdataRecorder.url.format(security_item.exchange, security_item.code, size)

        response = requests.get(url)
        response_json = demjson.decode(response.text)

        if response_json is None or len(response_json) == 0:
            return []

        df = pd.DataFrame(response_json)
        df.rename(columns={'day': 'timestamp'}, inplace=True)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df['name'] = security_item.name
        df['provider'] = 'sina'
        df['level'] = param['level']

        return df.to_dict(orient='records')


__all__ = ['ChinaETFDayKdataRecorder']

if __name__ == '__main__':
    init_log('sina_china_etf_day_kdata.log')
    ChinaETFDayKdataRecorder(level=IntervalLevel.LEVEL_1DAY).run()
