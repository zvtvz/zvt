# -*- coding: utf-8 -*-
import logging

from apscheduler.schedulers.background import BackgroundScheduler

from zvt import init_log

logger = logging.getLogger(__name__)

sched = BackgroundScheduler()


@sched.scheduled_job('cron', hour=18, minute=0)
def cal_ma_states():
    cal_ma_states(start='3000000', end='600000')


if __name__ == '__main__':
    init_log('ma_stats_runner3.log')

    cal_ma_states()

    sched.start()

    sched._thread.join()
