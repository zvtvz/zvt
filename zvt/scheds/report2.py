# -*- coding: utf-8 -*-
import logging
import time

from apscheduler.schedulers.background import BackgroundScheduler

from zvdata.api import get_entities
from zvdata.utils.time_utils import now_pd_timestamp, to_time_str
from zvt import init_log
from zvt.domain import Stock
from zvt.factors import GoodCompanyFactor
from zvt.factors.target_selector import TargetSelector
from zvt.informer.informer import EmailInformer

logger = logging.getLogger(__name__)

sched = BackgroundScheduler()


@sched.scheduled_job('cron', hour=16, minute=0)
def every_day_report():
    while True:
        try:
            t = now_pd_timestamp()
            if t.dayofweek in (5, 6):
                logger.info(f'today:{t} is {t.day_name()},just ignore')

            today = to_time_str(t)

            my_selector = TargetSelector(start_timestamp='2015-01-01', end_timestamp=today)
            # add the factors
            good_factor = GoodCompanyFactor(start_timestamp='2015-01-01', end_timestamp=today)

            my_selector.add_filter_factor(good_factor)
            my_selector.run()

            long_targets = my_selector.get_open_long_targets(today)
            if long_targets:
                long_targets = list(set(long_targets))
                df = get_entities(provider='eastmoney', entity_schema=Stock, entity_ids=long_targets,
                                  columns=['code', 'name'])
                info = [df.loc[i, 'code'] + ' ' + df.loc[i, 'name'] for i in df.index]
                msg = ' '.join(info)
            else:
                msg = 'no targets'

            logger.info(msg)

            email_action = EmailInformer()
            email_action.send_message("5533061@qq.com", f'{today} 基本面选股结果', msg)

            break
        except Exception as e:
            logger.exception('report2 sched error:{}'.format(e))
            time.sleep(60 * 3)


if __name__ == '__main__':
    init_log('report2.log')

    every_day_report()

    sched.start()

    sched._thread.join()
