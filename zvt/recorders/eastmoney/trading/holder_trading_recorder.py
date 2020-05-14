# -*- coding: utf-8 -*-
from zvt.utils.utils import to_float
from zvt.domain import HolderTrading

from zvt.recorders.eastmoney.common import EastmoneyMoreDataRecorder


class HolderTradingRecorder(EastmoneyMoreDataRecorder):
    data_schema = HolderTrading

    url = 'https://emh5.eastmoney.com/api/JiaoYiShuJu/GetGuDongZengJian'
    path_fields = ['GuDongZengJianList']

    def get_original_time_field(self):
        return 'RiQi'

    def get_data_map(self):
        return {
            "holder_name": ("GuDongMingCheng", str),
            "volume": ("BianDongShuLiang", to_float),
            "change_pct": ("BianDongBiLi", to_float),
            "holding_pct": ("BianDongHouChiGuBiLi", to_float)
        }

    def generate_domain_id(self, entity, original_data):
        the_name = original_data.get("GuDongMingCheng")
        timestamp = original_data[self.get_original_time_field()]
        the_id = "{}_{}_{}".format(entity.id, timestamp, the_name)
        return the_id


__all__ = ['HolderTradingRecorder']

if __name__ == '__main__':
    # init_log('holder_trading.log')

    recorder = HolderTradingRecorder(codes=['002572'])
    recorder.run()
