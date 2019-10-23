# -*- coding: utf-8 -*-

import logging
import time

from apscheduler.schedulers.background import BackgroundScheduler

from zvt.recorders.eastmoney.dividend_financing.dividend_detail_recorder import DividendDetailRecorder
from zvt.recorders.eastmoney.dividend_financing.dividend_financing_recorder import DividendFinancingRecorder
from zvt.recorders.eastmoney.dividend_financing.rights_issue_detail_recorder import RightsIssueDetailRecorder
from zvt.recorders.eastmoney.dividend_financing.spo_detail_recorder import SPODetailRecorder
from zvt import init_log

logger = logging.getLogger(__name__)

sched = BackgroundScheduler()


@sched.scheduled_job('cron', hour=2, minute=00)
def run():
    while True:
        try:
            DividendFinancingRecorder().run()
            RightsIssueDetailRecorder().run()
            SPODetailRecorder().run()
            DividendDetailRecorder().run()

            break
        except Exception as e:
            logger.exception('dividend_financing runner error:{}'.format(e))
            time.sleep(60)


if __name__ == '__main__':
    init_log('eastmoney_dividend_financing.log')

    run()

    sched.start()

    sched._thread.join()
