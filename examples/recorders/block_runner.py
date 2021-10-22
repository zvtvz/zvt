# -*- coding: utf-8 -*-
import logging
import time

from apscheduler.schedulers.background import BackgroundScheduler

from zvt import init_log, zvt_config
from zvt.domain import Block, Block1dKdata, BlockCategory
from zvt.informer.informer import EmailInformer

logger = logging.getLogger(__name__)

sched = BackgroundScheduler()


# 自行更改定定时运行时间
@sched.scheduled_job('cron', hour=17, minute=00, day_of_week=5)
def record_block():
    while True:
        email_action = EmailInformer()

        try:
            Block.record_data(provider='eastmoney')

            # 只抓去概念行情
            df = Block.query_data(filters=[Block.category == BlockCategory.concept.value], index='entity_id')
            entity_ids = df.index.tolist()
            Block1dKdata.record_data(provider='em', entity_ids=entity_ids)
            email_action.send_message(zvt_config['email_username'], 'record block finished', '')
            break
        except Exception as e:
            msg = f'record block error:{e}'
            logger.exception(msg)

            email_action.send_message(zvt_config['email_username'], 'record block error', msg)
            time.sleep(60)


if __name__ == '__main__':
    init_log('block_runner.log')

    record_block()

    sched.start()

    sched._thread.join()
