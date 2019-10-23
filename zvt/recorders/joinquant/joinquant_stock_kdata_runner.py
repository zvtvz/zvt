# -*- coding: utf-8 -*-
import logging
import time

from apscheduler.schedulers.background import BackgroundScheduler

from zvdata import IntervalLevel
from zvt import init_log
from zvt.recorders.joinquant.quotes.jq_stock_kdata_recorder import JQChinaStockKdataRecorder

logger = logging.getLogger(__name__)

sched = BackgroundScheduler()


@sched.scheduled_job('cron', hour=16, minute=0)
def run():
    while True:
        try:
            JQChinaStockKdataRecorder(level=IntervalLevel.LEVEL_1DAY).run()

            break
        except Exception as e:
            logger.exception('joinquant kdata runner error:{}'.format(e))
            time.sleep(60)


if __name__ == '__main__':
    init_log('joinquant_kdata_runner.log')

    run()

    sched.start()

    sched._thread.join()
