# -*- coding: utf-8 -*-
import logging
import time

from apscheduler.schedulers.background import BackgroundScheduler

from zvt import init_log
from zvt.domain import *
from zvt.informer.informer import EmailInformer

logger = logging.getLogger(__name__)

sched = BackgroundScheduler()


# 自行更改定定时运行时间
@sched.scheduled_job('cron', hour=1, minute=00, day_of_week=2)
def run():
    while True:
        email_action = EmailInformer()

        try:
            StockInstitutionalInvestorHolder.record_data(provider='em')
            StockTopTenFreeHolder.record_data(provider='em')
            StockActorSummary.record_data(provider='em')

            email_action.send_message("5533061@qq.com", 'em runner finished', '')
            break
        except Exception as e:
            msg = f'eastmoney runner1 error:{e}'
            logger.exception(msg)

            email_action.send_message("5533061@qq.com", 'em runner error', msg)
            time.sleep(60)


if __name__ == '__main__':
    init_log('em_data_runner.log')

    run()

    sched.start()

    sched._thread.join()
