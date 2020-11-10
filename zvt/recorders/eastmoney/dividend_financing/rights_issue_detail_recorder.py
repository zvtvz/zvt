# -*- coding: utf-8 -*-
from zvt.domain import RightsIssueDetail, DividendFinancing
from zvt.recorders.eastmoney.common import EastmoneyPageabeDataRecorder
from zvt.consts import SAMPLE_STOCK_CODES
from zvt.utils.pd_utils import pd_is_not_null
from zvt.utils.time_utils import now_pd_timestamp
from zvt.utils.utils import to_float


class RightsIssueDetailRecorder(EastmoneyPageabeDataRecorder):
    data_schema = RightsIssueDetail

    url = 'https://emh5.eastmoney.com/api/FenHongRongZi/GetPeiGuMingXiList'
    page_url = url
    path_fields = ['PeiGuMingXiList']

    def get_original_time_field(self):
        return 'PeiGuGongGaoRi'

    def get_data_map(self):
        return {
            "rights_issues": ("ShiJiPeiGu", to_float),
            "rights_issue_price": ("PeiGuJiaGe", to_float),
            "rights_raising_fund": ("ShiJiMuJi", to_float)
        }

    def on_finish(self):
        last_year = str(now_pd_timestamp().year)
        codes = [item.code for item in self.entities]
        need_filleds = DividendFinancing.query_data(provider=self.provider, codes=codes,
                                                    return_type='domain',
                                                    session=self.session,
                                                    filters=[DividendFinancing.rights_raising_fund.is_(None)],
                                                    end_timestamp=last_year)

        for item in need_filleds:
            df = RightsIssueDetail.query_data(provider=self.provider, entity_id=item.entity_id,
                                              columns=[RightsIssueDetail.timestamp,
                                                       RightsIssueDetail.rights_raising_fund],
                                              start_timestamp=item.timestamp,
                                              end_timestamp="{}-12-31".format(item.timestamp.year))
            if pd_is_not_null(df):
                item.rights_raising_fund = df['rights_raising_fund'].sum()
                self.session.commit()

        super().on_finish()


__all__ = ['RightsIssueDetailRecorder']

if __name__ == '__main__':
    # init_log('rights_issue.log')

    recorder = RightsIssueDetailRecorder(codes=SAMPLE_STOCK_CODES)
    recorder.run()
