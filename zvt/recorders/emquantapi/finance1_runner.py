# -*- coding: utf-8 -*-

import logging
import time

from apscheduler.schedulers.background import BackgroundScheduler

from zvt.recorders.eastmoney.finance.china_stock_balance_sheet_recorder import ChinaStockBalanceSheetRecorder
from zvt.recorders.eastmoney.finance.china_stock_income_statement_recorder import ChinaStockIncomeStatementRecorder
from zvt import init_log

logger = logging.getLogger(__name__)

sched = BackgroundScheduler()


@sched.scheduled_job('cron', hour=2, minute=00)
def run():
    while True:
        try:
            ChinaStockBalanceSheetRecorder().run()
            ChinaStockIncomeStatementRecorder().run()
            break
        except Exception as e:
            logger.exception('finance runner 1 error:{}'.format(e))
            time.sleep(60)


if __name__ == '__main__':
    init_log('eastmoney_balance_sheet_income_statement.log')

    run()

    sched.start()

    sched._thread.join()
