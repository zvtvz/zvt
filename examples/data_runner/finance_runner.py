# -*- coding: utf-8 -*-
import logging

from apscheduler.schedulers.background import BackgroundScheduler

from zvt import init_log
from zvt.domain import (
    Stock,
    StockDetail,
    FinanceFactor,
    BalanceSheet,
    IncomeStatement,
    CashFlowStatement,
)
from zvt.utils.recorder_utils import run_data_recorder

logger = logging.getLogger(__name__)

sched = BackgroundScheduler()


@sched.scheduled_job("cron", hour=1, minute=00, day_of_week=5)
def record_actor_data(data_provider="eastmoney", entity_provider="eastmoney"):
    run_data_recorder(domain=Stock, data_provider=data_provider)
    run_data_recorder(domain=StockDetail, data_provider=data_provider)
    run_data_recorder(domain=FinanceFactor, data_provider=data_provider, entity_provider=entity_provider, day_data=True)
    run_data_recorder(domain=BalanceSheet, data_provider=data_provider, entity_provider=entity_provider, day_data=True)
    run_data_recorder(
        domain=IncomeStatement, data_provider=data_provider, entity_provider=entity_provider, day_data=True
    )
    run_data_recorder(
        domain=CashFlowStatement, data_provider=data_provider, entity_provider=entity_provider, day_data=True
    )


if __name__ == "__main__":
    init_log("finance_runner.log")

    record_actor_data()

    sched.start()

    sched._thread.join()
