# -*- coding: utf-8 -*-
import logging
import time

from apscheduler.schedulers.background import BackgroundScheduler

from examples.utils import add_to_eastmoney
from zvt import init_log, zvt_config
from zvt.domain import Block, Block1dKdata, BlockCategory
from zvt.informer.informer import EmailInformer
from zvt.utils import current_date, next_date

logger = logging.getLogger(__name__)

sched = BackgroundScheduler()


# 自行更改定定时运行时间
@sched.scheduled_job('cron', hour=16, minute=00, day_of_week='mon-fri')
def record_block():
    while True:
        email_action = EmailInformer()

        try:
            Block.record_data(provider='eastmoney', force_update=False)

            # 抓取概念行情
            df = Block.query_data(filters=[Block.category == BlockCategory.concept.value], index='entity_id')
            entity_ids = df.index.tolist()
            Block1dKdata.record_data(provider='em', entity_ids=entity_ids, day_data=True)

            # 抓取行业行情
            df = Block.query_data(filters=[Block.category == BlockCategory.industry.value], index='entity_id')
            entity_ids = df.index.tolist()
            Block1dKdata.record_data(provider='em', entity_ids=entity_ids, day_data=True)

            # 报告新概念和行业
            list_date = next_date(current_date(), -90)
            df = Block.query_data(filters=[Block.category == BlockCategory.concept.value, Block.list_date >= list_date],
                                  index='entity_id')

            # add them to eastmoney
            try:
                add_to_eastmoney(codes=df['code'], entity_type='block', group='新概念', over_write=False)
            except Exception as e:
                email_action.send_message(zvt_config['email_username'], f'report_concept error',
                                          'report_concept error:{}'.format(e))

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
