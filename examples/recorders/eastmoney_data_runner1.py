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
# 这些数据都是些低频分散的数据，每天更新一次即可
@sched.scheduled_job('cron', hour=2, minute=00, day_of_week=5)
def run():
    while True:
        email_action = EmailInformer()

        try:
            Stock.record_data(provider='eastmoney')
            Stock.record_data(provider='joinquant')
            FinanceFactor.record_data(provider='eastmoney')
            BalanceSheet.record_data(provider='eastmoney')
            IncomeStatement.record_data(provider='eastmoney')
            CashFlowStatement.record_data(provider='eastmoney')

            email_action.send_message("5533061@qq.com", 'eastmoney recorder1 finished', '')
            break
        except Exception as e:
            msg = f'eastmoney recorder error:{e}'
            logger.exception(msg)

            email_action.send_message("5533061@qq.com", 'eastmoney recorder1 error', msg)
            time.sleep(60)


if __name__ == '__main__':
    init_log('eastmoney_data_runner1.log')

    run()

    sched.start()

    sched._thread.join()
