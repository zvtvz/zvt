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
            Stock.record_data(provider='joinquant')
            StockTradeDay.record_data(provider='joinquant')
            Stock1dKdata.record_data(provider='joinquant')
            StockValuation.record_data(provider='joinquant')

            Etf.record_data(provider='joinquant')
            EtfStock.record_data(provider='joinquant')

            email_action.send_message("5533061@qq.com", 'joinquant runner finished', '')
            break
        except Exception as e:
            msg = f'joinquant recorder error:{e}'
            logger.exception(msg)

            email_action.send_message("5533061@qq.com", 'joinquant runner error', msg)
            time.sleep(60)


if __name__ == '__main__':
    init_log('joinquant_data_runner.log')

    run()

    sched.start()

    sched._thread.join()
