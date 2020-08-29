# -*- coding: utf-8 -*-

import logging
import time

from apscheduler.schedulers.background import BackgroundScheduler

from zvt.recorders.eastmoney.trading.holder_trading_recorder import HolderTradingRecorder
from zvt.recorders.eastmoney.trading.manager_trading_recorder import ManagerTradingRecorder
from zvt import init_log

logger = logging.getLogger(__name__)

sched = BackgroundScheduler()


@sched.scheduled_job('cron', hour=1, minute=00)
def run():
    while True:
        try:
            HolderTradingRecorder().run()

            ManagerTradingRecorder().run()

            break
        except Exception as e:
            logger.exception('trading runner error:{}'.format(e))
            time.sleep(60)


if __name__ == '__main__':
    init_log('trading.log')

    run()

    sched.start()

    sched._thread.join()
