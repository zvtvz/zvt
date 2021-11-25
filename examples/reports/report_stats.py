# -*- coding: utf-8 -*-
import logging

from apscheduler.schedulers.background import BackgroundScheduler

from examples.report import report_top_stats
from zvt import init_log

logger = logging.getLogger(__name__)

sched = BackgroundScheduler()


@sched.scheduled_job('cron', hour=19, minute=30, day_of_week='mon-fri')
def report_stats():
    report_top_stats(entity_type='stock', entity_provider='joinquant', data_provider='joinquant')
    report_top_stats(entity_type='stockhk', entity_provider='em', data_provider='em')


if __name__ == '__main__':
    init_log('report_stats.log')

    report_stats()

    sched.start()

    sched._thread.join()
