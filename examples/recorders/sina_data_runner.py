# -*- coding: utf-8 -*-
import logging
import time

from apscheduler.schedulers.background import BackgroundScheduler

from zvt import init_log
from zvt.domain import *
from zvt.informer.informer import EmailInformer

logger = logging.getLogger(__name__)

sched = BackgroundScheduler()


@sched.scheduled_job('cron', hour=15, minute=30)
def run():
    while True:
        email_action = EmailInformer()

        try:
            Block.record_data(provider='sina')
            BlockStock.record_data(provider='sina')
            BlockMoneyFlow.record_data(provider='sina')

            email_action.send_message("5533061@qq.com", 'sina runner finished', '')
            break
        except Exception as e:
            msg = f'sina runner error:{e}'
            logger.exception(msg)

            email_action.send_message("5533061@qq.com", 'sina runner error', msg)
            time.sleep(60)


if __name__ == '__main__':
    init_log('sina_data_runner.log')

    run()

    sched.start()

    sched._thread.join()
