# -*- coding: utf-8 -*-
import logging

from apscheduler.schedulers.background import BackgroundScheduler

from examples.report import report_targets
from zvt import init_log
from zvt.contract import AdjustType
from zvt.factors import VolumeUpMaFactor

logger = logging.getLogger(__name__)

sched = BackgroundScheduler()


@sched.scheduled_job('cron', hour=19, minute=0, day_of_week='mon-fri')
def report_vol_up():
    report_targets(factor_cls=VolumeUpMaFactor, entity_provider='joinquant', data_provider='joinquant', em_group='年线股票',
                   title='放量突破(半)年线股票', entity_type='stock', em_group_over_write=True, filter_by_volume=True,
                   adjust_type=AdjustType.hfq, start_timestamp='2019-01-01',
                   # factor args
                   windows=[120, 250], over_mode='or', up_intervals=50, turnover_threshold=400000000)

    report_targets(factor_cls=VolumeUpMaFactor, entity_provider='eastmoney', data_provider='em', em_group='年线板块',
                   title='放量突破(半)年线板块', entity_type='block', em_group_over_write=False, filter_by_volume=False,
                   adjust_type=AdjustType.qfq, start_timestamp='2019-01-01',
                   # factor args
                   windows=[120, 250], over_mode='or', up_intervals=50, turnover_threshold=400000000)


if __name__ == '__main__':
    init_log('report_vol_up.log')

    report_vol_up()

    sched.start()

    sched._thread.join()
