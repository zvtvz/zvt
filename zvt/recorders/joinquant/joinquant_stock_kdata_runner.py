# -*- coding: utf-8 -*-
import logging
import time

from apscheduler.schedulers.background import BackgroundScheduler

from zvdata.utils.utils import init_process_log
from zvt.recorders.joinquant.quotes.jq_stock_kdata_recorder import JQChinaStockKdataRecorder

logger = logging.getLogger(__name__)

sched = BackgroundScheduler()


@sched.scheduled_job('cron', hour=9, minute=25)
def run():
    while True:
        try:
            JQChinaStockKdataRecorder().run()

            break
        except Exception as e:
            logger.exception('joinquant quote runner error:{}'.format(e))
            time.sleep(60)


if __name__ == '__main__':
    init_process_log('joinquant_quote_runner.log')

    run()

    sched.start()

    sched._thread.join()
