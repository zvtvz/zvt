# -*- coding: utf-8 -*-
from zvt.domain import SpoDetail

from zvt.recorders.joinquant.dividend_financing.base_jq_dividend_financing_recorder import \
    BaseJqDividendFinancingRecorder

spo_detail_map = {
    'spo_issues': 'spo_issues',#实际增发
    'spo_price': 'spo_price',#增发价格
    'spo_raising_fund': 'spo_raising_fund',#实际募集
}
# {
#             "spo_issues": ("ShiJiZengFa", to_float),  实际增发
#             "spo_price": ("ZengFaJiaGe", to_float),    增发价格
#             "spo_raising_fund": ("ShiJiMuJi", to_float)   实际募集
#         }


class SPODetailRecorder(BaseJqDividendFinancingRecorder):
    data_schema = SpoDetail
    data_type = 2

    def get_data_map(self):
        return spo_detail_map


__all__ = ['SPODetailRecorder']

if __name__ == '__main__':
    # init_log('spo_detail.log')

    recorder = SPODetailRecorder(codes=['000999'])
    recorder.run()
