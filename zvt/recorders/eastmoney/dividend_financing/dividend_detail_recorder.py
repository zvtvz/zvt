# -*- coding: utf-8 -*-
from zvt.utils.time_utils import to_pd_timestamp
from zvt.domain import DividendDetail
from zvt.recorders.eastmoney.common import EastmoneyPageabeDataRecorder


class DividendDetailRecorder(EastmoneyPageabeDataRecorder):
    data_schema = DividendDetail

    url = 'https://emh5.eastmoney.com/api/FenHongRongZi/GetFenHongSongZhuanList'
    page_url = url
    path_fields = ['FenHongSongZhuanList']

    def get_original_time_field(self):
        return 'GongGaoRiQi'

    def get_data_map(self):
        return {
            # 公告日
            "announce_date": ("GongGaoRiQi", to_pd_timestamp),
            # 股权登记日
            "record_date": ("GuQuanDengJiRi", to_pd_timestamp),
            # 除权除息日
            "dividend_date": ("ChuQuanChuXiRi", to_pd_timestamp),
            # 方案
            "dividend": ("FengHongFangAn", str)
        }


__all__ = ['DividendDetailRecorder']

if __name__ == '__main__':
    # init_log('dividend_detail.log')

    recorder = DividendDetailRecorder(codes=['601318'])
    recorder.run()
