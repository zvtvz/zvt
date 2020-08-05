# -*- coding: utf-8 -*-
from zvt.domain.fundamental.dividend_financing import DividendFinancing
from zvt.recorders.eastmoney.common import EastmoneyPageabeDataRecorder
from zvt.utils.utils import second_item_to_float


class DividendFinancingRecorder(EastmoneyPageabeDataRecorder):
    data_schema = DividendFinancing

    url = 'https://emh5.eastmoney.com/api/FenHongRongZi/GetLiNianFenHongRongZiList'
    page_url = url
    path_fields = ['LiNianFenHongRongZiList']

    def get_original_time_field(self):
        return 'ShiJian'

    def get_data_map(self):
        return {
            # 分红总额
            "dividend_money": ("FenHongZongE", second_item_to_float),
            # 新股
            "ipo_issues": ("XinGu", second_item_to_float),
            # 增发
            "spo_issues": ("ZengFa", second_item_to_float),
            # 配股
            "rights_issues": ("PeiFa", second_item_to_float)
        }

    def on_finish(self):
        try:
            code_security = {}
            for item in self.entities:
                code_security[item.code] = item

                need_fill_items = DividendFinancing.query_data(provider=self.provider, codes=list(code_security.keys()),
                                                           return_type='domain',
                                                           session=self.session,
                                                           filters=[
                                                               DividendFinancing.ipo_raising_fund.is_(None),
                                                               DividendFinancing.ipo_issues != 0])

                for need_fill_item in need_fill_items:
                    if need_fill_item:
                        need_fill_item.ipo_raising_fund = code_security[item.code].raising_fund
                        self.session.commit()
        except Exception as e:
            self.logger.exception(e)

        super().on_finish()


__all__ = ['DividendFinancingRecorder']

if __name__ == '__main__':
    # init_log('dividend_financing.log')

    recorder = DividendFinancingRecorder(codes=['000999'])
    recorder.run()
