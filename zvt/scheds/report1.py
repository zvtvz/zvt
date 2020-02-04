# -*- coding: utf-8 -*-
import logging
import time

from apscheduler.schedulers.background import BackgroundScheduler

from zvdata import IntervalLevel
from zvdata.api import get_entities
from zvdata.utils.time_utils import now_pd_timestamp, to_time_str
from zvt import init_log
from zvt.domain import Stock
from zvt.factors.ma.ma_factor import CrossMaFactor
from zvt.factors.target_selector import TargetSelector
from zvt.informer.informer import EmailInformer
from zvt.recorders.joinquant.quotes.jq_stock_kdata_recorder import JqChinaStockKdataRecorder

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

            # 抓取k线数据
            JqChinaStockKdataRecorder(level=IntervalLevel.LEVEL_1DAY).run()
            JqChinaStockKdataRecorder(level=IntervalLevel.LEVEL_1WEEK).run()
            JqChinaStockKdataRecorder(level=IntervalLevel.LEVEL_1MON).run()

            # 计算均线
            my_selector = TargetSelector(start_timestamp='2016-01-01', end_timestamp=today)
            # add the factors
            # 设置dry_run为True，因为我们只需要最近的数据，不需要加载全量数据进行回测
            ma_factor = CrossMaFactor(start_timestamp='2016-01-01', end_timestamp=today, dry_run=True)

            my_selector.add_filter_factor(ma_factor)

            my_selector.run()

            long_targets = my_selector.get_open_long_targets(timestamp=today)
            if long_targets:
                df = get_entities(provider='eastmoney', entity_schema=Stock, entity_ids=long_targets,
                                  columns=['code', 'name'])
                info = [df.loc[i, 'code'] + ' ' + df.loc[i, 'name'] for i in df.index]
                msg = ' '.join(info)
            else:
                msg = 'no targets'

            logger.info(msg)

            email_action = EmailInformer()
            email_action.send_message("5533061@qq.com", f'{today} 均线选股结果', msg)

            break
        except Exception as e:
            logger.exception('report1 sched error:{}'.format(e))
            time.sleep(60 * 3)


if __name__ == '__main__':
    init_log('report1.log')

    every_day_report()

    sched.start()

    sched._thread.join()
