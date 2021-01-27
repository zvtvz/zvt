# -*- coding: utf-8 -*-

import requests

from zvt.contract import IntervalLevel
from zvt.contract.api import get_entities
from zvt.contract.api import get_db_session
from zvt.contract.recorder import FixedCycleDataRecorder
from zvt.utils.time_utils import to_pd_timestamp, now_time_str, TIME_FORMAT_DAY1
from zvt.utils.utils import json_callback_param, to_float
from zvt.api.quote import generate_kdata_id, get_kdata_schema
from zvt.domain import Index, BlockCategory, Block


def level_flag(level: IntervalLevel):
    level = IntervalLevel(level)
    if level == IntervalLevel.LEVEL_1DAY:
        return 101
    if level == IntervalLevel.LEVEL_1WEEK:
        return 102
    if level == IntervalLevel.LEVEL_1MON:
        return 103

    assert False


# 抓取行业的日线,周线,月线数据，用于中期选行业
class ChinaStockKdataRecorder(FixedCycleDataRecorder):
    entity_provider: str = 'eastmoney'
    entity_schema = Block

    provider = 'eastmoney'
    url = 'https://push2his.eastmoney.com/api/qt/stock/kline/get?secid=90.{}&cb=fsdata1567673076&klt={}&fqt=0&lmt={}&end={}&iscca=1&fields1=f1%2Cf2%2Cf3%2Cf4%2Cf5&fields2=f51%2Cf52%2Cf53%2Cf54%2Cf55%2Cf56%2Cf57&ut=f057cbcbce2a86e2866ab8877db1d059&forcect=1&fsdata1567673076=fsdata1567673076'

    def __init__(self, entity_type='index', exchanges=None, entity_ids=None, codes=None, day_data=False, batch_size=10,
                 force_update=False, sleeping_time=10, default_size=10000, real_time=True, fix_duplicate_way='add',
                 start_timestamp=None, end_timestamp=None,
                 level=IntervalLevel.LEVEL_1WEEK, kdata_use_begin_time=False, close_hour=0, close_minute=0,
                 one_day_trading_minutes=24 * 60) -> None:
        self.data_schema = get_kdata_schema(entity_type=entity_type, level=level)
        super().__init__(entity_type, exchanges, entity_ids, codes, day_data, batch_size, force_update, sleeping_time,
                         default_size, real_time, fix_duplicate_way, start_timestamp, end_timestamp, close_hour,
                         close_minute, level, kdata_use_begin_time,
                         one_day_trading_minutes)

    def init_entities(self):
        self.entity_session = get_db_session(provider=self.entity_provider, data_schema=self.entity_schema)

        self.entities = get_entities(session=self.entity_session, entity_type='index',
                                     exchanges=self.exchanges,
                                     codes=self.codes,
                                     entity_ids=self.entity_ids,
                                     return_type='domain', provider=self.provider,
                                     # 只抓概念和行业
                                     filters=[Index.category.in_(
                                         [BlockCategory.industry.value, BlockCategory.concept.value])])

    def record(self, entity, start, end, size, timestamps):
        the_url = self.url.format("{}".format(entity.code), level_flag(self.level), size,
                                  now_time_str(fmt=TIME_FORMAT_DAY1))

        resp = requests.get(the_url)
        results = json_callback_param(resp.text)

        kdatas = []

        if results:
            klines = results['data']['klines']

            # TODO: ignore the last unfinished kdata now,could control it better if need
            for result in klines[:-1]:
                # "2000-01-28,1005.26,1012.56,1173.12,982.13,3023326,3075552000.00"
                # time,open,close,high,low,volume,turnover
                fields = result.split(',')
                the_timestamp = to_pd_timestamp(fields[0])

                the_id = generate_kdata_id(entity_id=entity.id, timestamp=the_timestamp, level=self.level)

                kdatas.append(dict(id=the_id,
                                   timestamp=the_timestamp,
                                   entity_id=entity.id,
                                   code=entity.code,
                                   name=entity.name,
                                   level=self.level.value,
                                   open=to_float(fields[1]),
                                   close=to_float(fields[2]),
                                   high=to_float(fields[3]),
                                   low=to_float(fields[4]),
                                   volume=to_float(fields[5]),
                                   turnover=to_float(fields[6])))
        return kdatas


__all__ = ['ChinaStockKdataRecorder']

if __name__ == '__main__':
    recorder = ChinaStockKdataRecorder(level=IntervalLevel.LEVEL_1MON)
    recorder.run()
