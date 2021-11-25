# -*- coding: utf-8 -*-
import logging
import time

from apscheduler.schedulers.background import BackgroundScheduler

from zvt import init_log, zvt_config
from zvt.domain import Stock, StockTradeDay, Stock1dHfqKdata, Stockhk, Stockhk1dHfqKdata
from zvt.informer.informer import EmailInformer

logger = logging.getLogger(__name__)

sched = BackgroundScheduler()


@sched.scheduled_job('cron', hour=6, minute=0)
def record_stock():
    while True:
        email_action = EmailInformer()

        try:
            # 股票
            Stock.record_data(provider='joinquant', sleeping_time=1)
            # 港股
            Stockhk.record_data(provider='em', force_update=False)
            # 交易日
            StockTradeDay.record_data(provider='joinquant', sleeping_time=1)

            email_action.send_message(zvt_config['email_username'], 'record stock, stockhk finished', '')
            break
        except Exception as e:
            msg = f'record stock:{e}'
            logger.exception(msg)

            email_action.send_message(zvt_config['email_username'], 'record stock error', msg)
            time.sleep(60 * 5)


@sched.scheduled_job('cron', hour=16, minute=30)
def record_kdata():
    while True:
        email_action = EmailInformer()

        try:
            # A股日线
            Stock1dHfqKdata.record_data(provider='joinquant', sleeping_time=0, day_data=True)
            # 港股通日线
            df = Stockhk.query_data(filters=[Stockhk.south == True], index='entity_id')
            Stockhk1dHfqKdata.record_data(entity_ids=df.index.tolist(), provider='em', day_data=True)

            email_action.send_message(zvt_config['email_username'], 'record kdata finished', '')
            break
        except Exception as e:
            msg = f'record kdata:{e}'
            logger.exception(msg)

            email_action.send_message(zvt_config['email_username'], 'record kdata error', msg)
            time.sleep(60 * 5)


if __name__ == '__main__':
    init_log('day_kdata_runner.log')

    record_kdata()

    sched.start()

    sched._thread.join()
