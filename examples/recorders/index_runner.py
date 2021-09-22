# -*- coding: utf-8 -*-
import logging
import time

from apscheduler.schedulers.background import BackgroundScheduler

from zvt import init_log, zvt_config
from zvt.domain import Index, Index1dKdata, IndexStock
from zvt.informer.informer import EmailInformer

logger = logging.getLogger(__name__)

sched = BackgroundScheduler()


# 自行更改定定时运行时间
@sched.scheduled_job('cron', hour=1, minute=00, day_of_week=3)
def run():
    while True:
        email_action = EmailInformer()

        try:
            Index.record_data(provider='exchange')
            IndexStock.record_data(provider='exchange')
            Index1dKdata.record_data(provider='em')
            email_action.send_message(zvt_config['email_username'], 'index runner finished', '')
            break
        except Exception as e:
            msg = f'index runner error:{e}'
            logger.exception(msg)

            email_action.send_message(zvt_config['email_username'], 'index runner error', msg)
            time.sleep(60)


if __name__ == '__main__':
    init_log('index_runner.log')

    run()

    sched.start()

    sched._thread.join()
