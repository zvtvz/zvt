# -*- coding: utf-8 -*-
from zvt.utils.utils import to_float
from zvt.domain import ManagerTrading

from zvt.recorders.eastmoney.common import EastmoneyMoreDataRecorder


class ManagerTradingRecorder(EastmoneyMoreDataRecorder):
    data_schema = ManagerTrading

    url = 'https://emh5.eastmoney.com/api/JiaoYiShuJu/GetGaoGuanZengJian'
    path_fields = ['GaoGuanZengJianList']

    def get_original_time_field(self):
        return 'RiQi'

    def get_data_map(self):
        return {
            "trading_person": ("BianDongRen", str),
            "volume": ("BianDongShuLiang", to_float),
            "price": ("JiaoYiJunJia", to_float),
            "holding": ("BianDongHouShuLiang", to_float),
            "trading_way": ("JiaoYiTuJing", str),
            "manager": ("GaoGuanMingCheng", str),
            "manager_position": ("GaoGuanZhiWei", str),
            "relationship_with_manager": ("GaoGuanGuanXi", str),
        }

    def generate_domain_id(self, entity, original_data):
        the_name = original_data.get("BianDongRen")
        timestamp = original_data[self.get_original_time_field()]
        the_id = "{}_{}_{}".format(entity.id, timestamp, the_name)
        return the_id


__all__ = ['ManagerTradingRecorder']

if __name__ == '__main__':
    # init_log('manager_trading.log')

    recorder = ManagerTradingRecorder(codes=['002572'])
    recorder.run()
