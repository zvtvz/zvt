# -*- coding: utf-8 -*-
import logging
import time

from apscheduler.schedulers.background import BackgroundScheduler

from zvdata import IntervalLevel
from zvdata.utils.utils import init_process_log
from zvt.recorders.joinquant.quotes.jq_stock_bar_recorder import JQChinaStockBarRecorder

logger = logging.getLogger(__name__)

sched = BackgroundScheduler()


# 每周6抓取周线和月线数据
@sched.scheduled_job('cron', day_of_week=5, hour=3, minute=0)
def run():
    while True:
        try:
            JQChinaStockBarRecorder(level=IntervalLevel.LEVEL_1WEEK).run()
            JQChinaStockBarRecorder(level=IntervalLevel.LEVEL_1MON).run()

            break
        except Exception as e:
            logger.exception('joinquant bar runner error:{}'.format(e))
            time.sleep(60)


if __name__ == '__main__':
    init_process_log('joinquant_bar_runner.log')

    run()

    sched.start()

    sched._thread.join()
