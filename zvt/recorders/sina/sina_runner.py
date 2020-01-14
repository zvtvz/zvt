# -*- coding: utf-8 -*-
import logging
import time

from apscheduler.schedulers.background import BackgroundScheduler

from zvt import init_log
from zvt.recorders.sina.meta.sina_china_stock_category_recorder import SinaChinaBlockRecorder
from zvt.recorders.sina.money_flow import SinaBlockMoneyFlowRecorder

logger = logging.getLogger(__name__)

sched = BackgroundScheduler()


@sched.scheduled_job('cron', hour=17, minute=00)
def run():
    while True:
        try:
            SinaChinaBlockRecorder().run()

            SinaBlockMoneyFlowRecorder().run()
            break
        except Exception as e:
            logger.exception('sina runner error:{}'.format(e))
            time.sleep(60)


if __name__ == '__main__':
    init_log('sina_runner.log')

    run()

    sched.start()

    sched._thread.join()
