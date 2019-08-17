# -*- coding: utf-8 -*-

import logging
import time

from apscheduler.schedulers.background import BackgroundScheduler

from zvt.recorders.eastmoney.finance.china_stock_balance_sheet_recorder import ChinaStockBalanceSheetRecorder
from zvt.recorders.eastmoney.finance.china_stock_cash_flow_recorder import ChinaStockCashFlowRecorder
from zvt.recorders.eastmoney.finance.china_stock_finance_factor_recorder import ChinaStockFinanceFactorRecorder
from zvt.recorders.eastmoney.finance.china_stock_income_statement_recorder import ChinaStockIncomeStatementRecorder
from zvt.utils.utils import init_process_log

logger = logging.getLogger(__name__)

sched = BackgroundScheduler()


@sched.scheduled_job('cron', hour=2, minute=00)
def run():
    while True:
        try:
            ChinaStockFinanceFactorRecorder().run()
            ChinaStockCashFlowRecorder().run()
            ChinaStockBalanceSheetRecorder().run()
            ChinaStockIncomeStatementRecorder().run()
            break
        except Exception as e:
            logger.exception('finance runner error:{}'.format(e))
            time.sleep(60)


if __name__ == '__main__':
    init_process_log('finance.log')

    run()

    sched.start()

    sched._thread.join()
