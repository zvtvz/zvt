# -*- coding: utf-8 -*-
import logging

from apscheduler.schedulers.background import BackgroundScheduler

from zvt import init_log
from zvt.factors.ma.common import cal_ma_states

logger = logging.getLogger(__name__)

sched = BackgroundScheduler()


@sched.scheduled_job('cron', hour=20, minute=0)
def run():
    cal_ma_states(start='600200', end='601000')


if __name__ == '__main__':
    init_log('ma_stats_runner5.log')

    run()

    sched.start()

    sched._thread.join()
