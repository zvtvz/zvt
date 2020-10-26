# -*- coding: utf-8 -*-
from zvt.domain.fundamental.dividend_financing import DividendFinancing
from zvt.recorders.joinquant.dividend_financing.base_jq_dividend_financing_recorder import BaseJqDividendFinancingRecorder
dividend_financing_map={
    # 分红总额
    'dividend_money' :'bonus_amount_rmb',
    # 新股
    'ipo_issues' :'ipo_shares',
    # IPO募集资金
    'ipo_raising_fund' :'ipo_raising_fund',
    # 增发
    'spo_issues' :'spo_issues',
    'spo_raising_fund' :'spo_raising_fund',
    # 配股
    'rights_issues' :'rights_issues',
    'rights_raising_fund' :'rights_raising_fund',
}
# {
#             分红总额
            # "dividend_money": ("FenHongZongE", second_item_to_float),
            # 新股
            # "ipo_issues": ("XinGu", second_item_to_float),
            # 增发
            # "spo_issues": ("ZengFa", second_item_to_float),
            # 配股
            # "rights_issues": ("PeiFa", second_item_to_float)
        # }

class JqDividendFinancingRecorder(BaseJqDividendFinancingRecorder):
    data_schema = DividendFinancing

    data_type = 2


    def get_data_map(self):
        return dividend_financing_map


__all__ = ['JqDividendFinancingRecorder']

if __name__ == '__main__':
    # init_log('shares_change.log')

    recorder = JqDividendFinancingRecorder(codes=['000999'])
    recorder.run()
