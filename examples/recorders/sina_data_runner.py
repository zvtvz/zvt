# -*- coding: utf-8 -*-
import logging
import time

from apscheduler.schedulers.background import BackgroundScheduler

from zvt import init_log
from zvt.domain import *
from zvt.informer.informer import EmailInformer

logger = logging.getLogger(__name__)

sched = BackgroundScheduler()


@sched.scheduled_job('cron', hour=15, minute=30, day_of_week=3)
def record_block():
    while True:
        email_action = EmailInformer()

        try:
            Block.record_data(provider='sina')
            BlockStock.record_data(provider='sina')

            email_action.send_message("5533061@qq.com", 'sina block finished', '')
            break
        except Exception as e:
            msg = f'sina block error:{e}'
            logger.exception(msg)

            email_action.send_message("5533061@qq.com", 'sina block error', msg)
            time.sleep(60)


@sched.scheduled_job('cron', hour=15, minute=30)
def record_money_flow():
    while True:
        email_action = EmailInformer()

        try:
            BlockMoneyFlow.record_data(provider='sina')

            email_action.send_message("5533061@qq.com", 'sina money flow finished', '')
            break
        except Exception as e:
            msg = f'sina money flow error:{e}'
            logger.exception(msg)

            email_action.send_message("5533061@qq.com", 'sina money flow error', msg)
            time.sleep(60)


if __name__ == '__main__':
    init_log('sina_data_runner.log')

    record_block()
    record_money_flow()

    sched.start()

    sched._thread.join()
