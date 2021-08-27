# -*- coding: utf-8 -*-
import logging
import time

from apscheduler.schedulers.background import BackgroundScheduler

from zvt import init_log, zvt_config
from zvt.domain import Stock, StockTradeDay, Stock1dHfqKdata
from zvt.informer.informer import EmailInformer

logger = logging.getLogger(__name__)

sched = BackgroundScheduler()


@sched.scheduled_job('cron', hour=6, minute=0)
def record_stock():
    while True:
        email_action = EmailInformer()

        try:
            Stock.record_data(provider='joinquant', sleeping_time=1)
            StockTradeDay.record_data(provider='joinquant', sleeping_time=1)
            email_action.send_message(zvt_config['email_username'], 'joinquant record stock finished', '')
            break
        except Exception as e:
            msg = f'joinquant record stock:{e}'
            logger.exception(msg)

            email_action.send_message(zvt_config['email_username'], 'joinquant record stock error', msg)
            time.sleep(60 * 5)


@sched.scheduled_job('cron', hour=15, minute=20)
def record_kdata():
    while True:
        email_action = EmailInformer()

        try:
            # 日线前复权和后复权数据
            # Stock1dKdata.record_data(provider='joinquant', sleeping_time=0)
            Stock1dHfqKdata.record_data(provider='joinquant', sleeping_time=0, day_data=True)
            # StockMoneyFlow.record_data(provider='joinquant', sleeping_time=0)
            # IndexMoneyFlow.record_data(provider='joinquant', sleeping_time=0)
            email_action.send_message(zvt_config['email_username'], 'joinquant record kdata finished', '')
            break
        except Exception as e:
            msg = f'joinquant record kdata:{e}'
            logger.exception(msg)

            email_action.send_message(zvt_config['email_username'], 'joinquant record kdata error', msg)
            time.sleep(60 * 5)


if __name__ == '__main__':
    init_log('joinquant_kdata_runner.log')

    record_kdata()

    sched.start()

    sched._thread.join()
