# -*- coding: utf-8 -*-
from zvt.utils.time_utils import to_time_str, to_pd_timestamp
from zvt.utils.utils import to_float
from zvt.api.quote import to_report_period_type
from zvt.domain.misc.holder import TopTenHolder
from zvt.recorders.eastmoney.common import EastmoneyTimestampsDataRecorder, get_fc


class TopTenHolderRecorder(EastmoneyTimestampsDataRecorder):
    provider = 'eastmoney'
    data_schema = TopTenHolder

    url = 'https://emh5.eastmoney.com/api/GuBenGuDong/GetShiDaGuDong'
    path_fields = ['ShiDaGuDongList']

    timestamps_fetching_url = 'https://emh5.eastmoney.com/api/GuBenGuDong/GetFirstRequest2Data'
    timestamp_list_path_fields = ['SDGDBGQ', 'ShiDaGuDongBaoGaoQiList']
    timestamp_path_fields = ['BaoGaoQi']

    def get_data_map(self):
        return {
            "report_period": ("timestamp", to_report_period_type),
            "report_date": ("timestamp", to_pd_timestamp),
            # 股东代码
            "holder_code": ("GuDongDaiMa", str),
            # 股东名称
            "holder_name": ("GuDongMingCheng", str),
            # 持股数
            "shareholding_numbers": ("ChiGuShu", to_float),
            # 持股比例
            "shareholding_ratio": ("ChiGuBiLi", to_float),
            # 变动
            "change": ("ZengJian", to_float),
            # 变动比例
            "change_ratio": ("BianDongBiLi", to_float),
        }

    def generate_request_param(self, security_item, start, end, size, timestamp):
        return {"color": "w",
                "fc": get_fc(security_item),
                "BaoGaoQi": to_time_str(timestamp)
                }

    def generate_domain_id(self, entity, original_data):
        the_name = original_data.get("GuDongMingCheng")
        timestamp = original_data[self.get_original_time_field()]
        the_id = "{}_{}_{}".format(entity.id, timestamp, the_name)
        return the_id


__all__ = ['TopTenHolder']

if __name__ == '__main__':
    # init_log('top_ten_holder.log')

    TopTenHolderRecorder(codes=['002572']).run()
