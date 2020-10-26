# -*- coding: utf-8 -*-
from zvt.domain import RightsIssueDetail

from zvt.settings import SAMPLE_STOCK_CODES
from zvt.recorders.joinquant.dividend_financing.base_jq_dividend_financing_recorder import \
    BaseJqDividendFinancingRecorder

rights_issue_detail_map = {
    # 配股
    'rights_issues': 'rights_issues',  # 实际配股
    'rights_issue_price': 'rights_issue_price',  # 配股价格
    'rights_raising_fund': 'rights_raising_fund',  # 实际募集
}


class RightsIssueDetailRecorder(BaseJqDividendFinancingRecorder):
    data_schema = RightsIssueDetail
    data_type = 2

    def get_data_map(self):
        return rights_issue_detail_map


__all__ = ['RightsIssueDetailRecorder']

if __name__ == '__main__':
    # init_log('rights_issue.log')

    recorder = RightsIssueDetailRecorder(codes=SAMPLE_STOCK_CODES)
    recorder.run()
