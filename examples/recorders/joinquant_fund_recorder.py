# -*- coding: utf-8 -*-
import logging
import time

from apscheduler.schedulers.background import BackgroundScheduler

from zvt import init_log
from zvt.domain import Fund, FundStock, Stock1wkHfqKdata
from zvt.informer.informer import EmailInformer

logger = logging.getLogger(__name__)

sched = BackgroundScheduler()


# 周4抓取
@sched.scheduled_job('cron', hour=19, minute=00, day_of_week=3)
def record_fund():
    while True:
        email_action = EmailInformer()

        try:
            # 基金和基金持仓数据
            Fund.record_data(provider='joinquant', sleeping_time=1)
            FundStock.record_data(provider='joinquant', sleeping_time=1)
            # 股票周线后复权数据
            Stock1wkHfqKdata.record_data(provider='joinquant', sleeping_time=0)

            email_action.send_message("5533061@qq.com", 'joinquant record fund finished', '')
            break
        except Exception as e:
            msg = f'joinquant record fund error:{e}'
            logger.exception(msg)

            email_action.send_message("5533061@qq.com", 'joinquant record fund error', msg)
            time.sleep(60)


if __name__ == '__main__':
    init_log('joinquant_fund_runner.log')

    record_fund()

    sched.start()

    sched._thread.join()
