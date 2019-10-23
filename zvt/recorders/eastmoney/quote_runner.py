# -*- coding: utf-8 -*-
import logging
import time

from apscheduler.schedulers.background import BackgroundScheduler

from zvdata import IntervalLevel
from zvt import init_log
from zvt.recorders.eastmoney.quotes.china_stock_kdata_recorder import ChinaStockKdataRecorder

logger = logging.getLogger(__name__)

sched = BackgroundScheduler()


@sched.scheduled_job('cron', hour=16, minute=00)
def run():
    while True:
        try:
            week_kdata = ChinaStockKdataRecorder(level=IntervalLevel.LEVEL_1WEEK)
            week_kdata.run()

            mon_kdata = ChinaStockKdataRecorder(level=IntervalLevel.LEVEL_1MON)
            mon_kdata.run()

            break
        except Exception as e:
            logger.exception('quote runner error:{}'.format(e))
            time.sleep(60)


if __name__ == '__main__':
    init_log('eastmoney_quote.log')

    run()

    sched.start()

    sched._thread.join()
