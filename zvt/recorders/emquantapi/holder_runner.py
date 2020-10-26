# -*- coding: utf-8 -*-

import logging
import time

from apscheduler.schedulers.background import BackgroundScheduler

from zvt.recorders.eastmoney.holder.top_ten_holder_recorder import TopTenHolderRecorder
from zvt.recorders.eastmoney.holder.top_ten_tradable_holder_recorder import TopTenTradableHolderRecorder
from zvt import init_log

logger = logging.getLogger(__name__)

sched = BackgroundScheduler()


@sched.scheduled_job('cron', hour=1, minute=00)
def run():
    while True:
        try:
            TopTenHolderRecorder().run()

            TopTenTradableHolderRecorder().run()
            break
        except Exception as e:
            logger.exception('holder runner error:{}'.format(e))
            time.sleep(60)


if __name__ == '__main__':
    init_log('eastmoney_holder.log')

    run()

    sched.start()

    sched._thread.join()
