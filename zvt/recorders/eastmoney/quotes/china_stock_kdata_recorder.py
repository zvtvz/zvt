# -*- coding: utf-8 -*-

import requests

from zvt.api.common import data_exist, generate_kdata_id
from zvt.domain import IntervalLevel, EntityType
from zvt.recorders.recorder import TimeSeriesFetchingStyle, FixedCycleDataRecorder
from zvt.utils.time_utils import to_pd_timestamp, now_time_str, TIME_FORMAT_MINUTE
from zvt.utils.utils import json_callback_param, to_float


def eastmoney_map_zvt_trading_level(trading_level: IntervalLevel):
    if trading_level == IntervalLevel.LEVEL_1DAY:
        return 'k'
    if trading_level == IntervalLevel.LEVEL_1WEEK:
        return 'wk'
    if trading_level == IntervalLevel.LEVEL_5MIN:
        return 'M5K'


# 东方财富最多只能抓取最近的570条数据
# 主要用于抓取小级别(5分钟)实时数据
class ChinaStockKdataRecorder(FixedCycleDataRecorder):
    provider = 'eastmoney'
    url = 'https://pdfm.eastmoney.com/EM_UBG_PDTI_Fast/api/js?id={}&TYPE={}&js=fsdata1545726667((x))&rtntype=4&QueryStyle=2.2&QuerySpan={}%2C{}&isCR=false&fsdata1545726667=fsdata1545726667'

    def __init__(self, entity_type='stock', exchanges=['sh', 'sz'], codes=None, batch_size=10,
                 force_update=False, sleeping_time=5, fetching_style=TimeSeriesFetchingStyle.end_size,
                 default_size=2000, contain_unfinished_data=False, level=IntervalLevel.LEVEL_1HOUR,
                 one_shot=False) -> None:
        super().__init__(entity_type, exchanges, codes, batch_size, force_update, sleeping_time, fetching_style,
                         default_size, contain_unfinished_data, level, one_shot)

    def record(self, entity, start, end, size, time_array):
        if entity.type == 'index':
            id_flag = "{}1".format(entity.code)
        elif entity.type == 'stock':
            if entity.exchange == 'sh':
                id_flag = "{}1".format(entity.code)
            if entity.exchange == 'sz':
                id_flag = "{}2".format(entity.code)

        the_url = self.url.format("{}".format(id_flag), eastmoney_map_zvt_trading_level(self.level),
                                  now_time_str(fmt=TIME_FORMAT_MINUTE), size)

        resp = requests.get(the_url)
        results = json_callback_param(resp.text)

        kdatas = []

        for result in results:
            the_timestamp = to_pd_timestamp(result['time'])
            the_id = generate_kdata_id(entity_id=entity.id, timestamp=the_timestamp, level=self.level)

            if not data_exist(self.session, self.kdata_schema, the_id):
                kdatas.append(self.kdata_schema(id=the_id,
                                                timestamp=the_timestamp,
                                                entity_id=entity.id,
                                                code=entity.code,
                                                name=entity.name,
                                                level=self.level,
                                                open=to_float(result['open']),
                                                close=to_float(result['close']),
                                                high=to_float(result['high']),
                                                low=to_float(result['low']),
                                                volume=to_float(result['volume']),
                                                turnover=to_float(result['amount']),
                                                turnover_rate=to_float(result['turnoverrate'])
                                                ))
        return kdatas


if __name__ == '__main__':
    recorder = ChinaStockKdataRecorder(entity_type='stock', exchanges=['sh', 'sz'], codes=['000778'],
                                       level=IntervalLevel.LEVEL_5MIN)
    recorder.run()
