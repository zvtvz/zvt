# -*- coding: utf-8 -*-
from zvt.domain import TopTenTradableHolder
from zvt.recorders.eastmoney.holder.top_ten_holder_recorder import TopTenHolderRecorder


class TopTenTradableHolderRecorder(TopTenHolderRecorder):
    provider = 'eastmoney'
    data_schema = TopTenTradableHolder

    url = 'https://emh5.eastmoney.com/api/GuBenGuDong/GetShiDaLiuTongGuDong'
    path_fields = ['ShiDaLiuTongGuDongList']
    timestamps_fetching_url = 'https://emh5.eastmoney.com/api/GuBenGuDong/GetFirstRequest2Data'
    timestamp_list_path_fields = ['SDLTGDBGQ', 'ShiDaLiuTongGuDongBaoGaoQiList']
    timestamp_path_fields = ['BaoGaoQi']


__all__ = ['TopTenTradableHolderRecorder']

if __name__ == '__main__':
    # init_log('top_ten_tradable_holder.log')

    TopTenTradableHolderRecorder(codes=['002572']).run()
