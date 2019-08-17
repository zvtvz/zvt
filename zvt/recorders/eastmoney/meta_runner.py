# -*- coding: utf-8 -*-

import logging
import time

from apscheduler.schedulers.background import BackgroundScheduler

from zvt.domain import Provider
from zvt.recorders.common.china_stock_list_spider import ChinaStockListSpider
from zvt.recorders.eastmoney.meta.china_stock_category_recorder import ChinaStockCategoryRecorder
from zvt.recorders.eastmoney.meta.china_stock_meta_recorder import ChinaStockMetaRecorder
from zvt.utils.utils import init_process_log

logger = logging.getLogger(__name__)

sched = BackgroundScheduler()


@sched.scheduled_job('cron', hour=1, minute=00)
def run():
    while True:
        try:
            ChinaStockListSpider(provider='eastmoney').run()

            ChinaStockCategoryRecorder().run()

            ChinaStockMetaRecorder().run()
            break
        except Exception as e:
            logger.exception('meta runner error:{}'.format(e))
            time.sleep(60)


if __name__ == '__main__':
    init_process_log('eastmoney_china_stock_meta.log')

    run()

    sched.start()

    sched._thread.join()
