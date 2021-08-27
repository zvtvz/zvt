# -*- coding: utf-8 -*-
import logging
import time

from apscheduler.schedulers.background import BackgroundScheduler

from zvt import init_log, zvt_config
from zvt.domain import *
from zvt.informer.informer import EmailInformer

logger = logging.getLogger(__name__)

sched = BackgroundScheduler()


# 自行更改定定时运行时间
# 这些数据都是些低频分散的数据，每天更新一次即可
@sched.scheduled_job('cron', hour=2, minute=00, day_of_week=4)
def run():
    while True:
        email_action = EmailInformer()

        try:
            # DividendFinancing.record_data(provider='eastmoney')
            # HolderTrading.record_data(provider='eastmoney')
            # ManagerTrading.record_data(provider='eastmoney')
            TopTenHolder.record_data(provider='eastmoney')
            TopTenTradableHolder.record_data(provider='eastmoney')

            email_action.send_message(zvt_config['email_username'], 'eastmoney runner2 finished', '')
            break
        except Exception as e:
            msg = f'eastmoney runner2 error:{e}'
            logger.exception(msg)

            email_action.send_message(zvt_config['email_username'], 'eastmoney runner2 error', msg)
            time.sleep(60)


if __name__ == '__main__':
    init_log('eastmoney_data_runner2.log')

    run()

    sched.start()

    sched._thread.join()
