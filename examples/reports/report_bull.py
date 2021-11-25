# -*- coding: utf-8 -*-
import logging

from apscheduler.schedulers.background import BackgroundScheduler

from examples.report import report_targets
from zvt import init_log
from zvt.contract import AdjustType
from zvt.factors import MacdFactor
from zvt.factors.transformers import CrossMaTransformer

logger = logging.getLogger(__name__)

sched = BackgroundScheduler()


class BullAndUpFactor(MacdFactor):
    def compute_result(self):
        super().compute_result()
        t = CrossMaTransformer(windows=[5, 120, 250])
        self.factor_df = t.transform(self.factor_df)
        s = self.factor_df['turnover'] > 400000000
        self.result_df = (self.factor_df['filter_result'] & self.factor_df['bull'] & s).to_frame(name='filter_result')


@sched.scheduled_job('cron', hour=18, minute=30, day_of_week='mon-fri')
def report_bull():
    report_targets(factor_cls=BullAndUpFactor, entity_provider='joinquant', data_provider='joinquant',
                   title='bull股票', entity_type='stock', em_group='bull股票', em_group_over_write=True,
                   filter_by_volume=True, adjust_type=AdjustType.hfq, start_timestamp='2019-01-01')
    report_targets(factor_cls=BullAndUpFactor, entity_provider='eastmoney', data_provider='em',
                   title='bull板块', entity_type='block', em_group='bull板块', em_group_over_write=True,
                   filter_by_volume=False, adjust_type=AdjustType.qfq, start_timestamp='2019-01-01')
    report_targets(factor_cls=BullAndUpFactor, entity_provider='em', data_provider='em', em_group='自选股',
                   title='bull港股', entity_type='stockhk', em_group_over_write=False, filter_by_volume=False,
                   adjust_type=AdjustType.hfq, start_timestamp='2019-01-01')



if __name__ == '__main__':
    init_log('report_bull.log')

    report_bull()

    sched.start()

    sched._thread.join()
