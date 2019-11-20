# -*- coding: utf-8 -*-
import logging
import time

from apscheduler.schedulers.background import BackgroundScheduler

from zvdata.api import get_entities
from zvdata.utils.time_utils import now_pd_timestamp
from zvt import init_log
from zvt.domain import Stock
from zvt.factors import TargetSelector
from zvt.factors.ma.ma_factor import CrossMaFactor
from zvt.informer.informer import EmailInformer
from zvt.scheds import select_by_finance

logger = logging.getLogger(__name__)

sched = BackgroundScheduler()


@sched.scheduled_job('cron', hour=18, minute=50)
def every_day_report():
    while True:
        try:
            today = now_pd_timestamp()
            long_targets = select_by_finance(today)

            logger.info(f'selected:{len(long_targets)}')

            if long_targets:
                ma_factor = CrossMaFactor(start_timestamp='2015-01-01', end_timestamp=today, dry_run=True,
                                          persist_factor=False, entity_ids=long_targets, windows=[5, 30, 120])
                my_selector = TargetSelector(start_timestamp='2015-01-01', end_timestamp=today, entity_ids=long_targets)
                my_selector.add_filter_factor(ma_factor)
                my_selector.run()
                final_targets = my_selector.get_open_long_targets(today)

                final_targets = list(set(final_targets))

                logger.info(f'final selected:{len(final_targets)}')

                if final_targets:
                    df = get_entities(provider='eastmoney', entity_schema=Stock, entity_ids=final_targets,
                                      columns=['code', 'name'])
                    info = [df.loc[i, 'code'] + ' ' + df.loc[i, 'name'] for i in df.index]
                    msg = ' '.join(info)
            else:
                msg = 'no targets'

            logger.info(msg)

            email_action = EmailInformer()
            email_action.send_message("5533061@qq.com", f'{today} 基本面 + 技术面选股结果', msg)

            break
        except Exception as e:
            logger.exception('report3 sched error:{}'.format(e))
            time.sleep(60 * 3)


if __name__ == '__main__':
    init_log('report3.log')

    every_day_report()

    sched.start()

    sched._thread.join()
