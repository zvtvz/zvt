# -*- coding: utf-8 -*-

from zvt.domain import DividendDetail
from zvt.recorders.joinquant.dividend_financing.base_jq_dividend_financing_recorder import BaseJqDividendFinancingRecorder

dividend_detail_map={


}
class JqDividendDetailRecorder(BaseJqDividendFinancingRecorder):
    data_schema = DividendDetail
    # 分红配股
    data_type = 3
    def get_data_map(self):
        return dividend_detail_map


__all__ = ['JqDividendDetailRecorder']

if __name__ == '__main__':
    # init_log('dividend_detail.log')

    recorder = JqDividendDetailRecorder(codes=['601318'])
    recorder.run()
