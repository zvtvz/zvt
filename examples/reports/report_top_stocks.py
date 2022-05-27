# -*- coding: utf-8 -*-
import logging

from apscheduler.schedulers.background import BackgroundScheduler

from examples.report_utils import report_top_entities
from zvt import init_log
from zvt.api import TopType

logger = logging.getLogger(__name__)

sched = BackgroundScheduler()


@sched.scheduled_job("cron", hour=17, minute=0, day_of_week="mon-fri")
def report_top_stocks():
    report_top_entities(
        entity_type="stock",
        entity_provider="em",
        data_provider="em",
        periods=[3, 8, 30],
        ignore_new_stock=True,
        adjust_type=None,
        top_count=20,
        turnover_threshold=400000000,
        turnover_rate_threshold=0.02,
        em_group_over_write=True,
        return_type=TopType.positive,
    )
    report_top_entities(
        entity_type="stock",
        entity_provider="em",
        data_provider="em",
        periods=[365],
        ignore_new_stock=True,
        adjust_type=None,
        top_count=30,
        turnover_threshold=200000000,
        turnover_rate_threshold=0.02,
        em_group_over_write=True,
        return_type=TopType.negative,
    )


if __name__ == "__main__":
    init_log("report_top_stocks.log")

    report_top_stocks()

    sched.start()

    sched._thread.join()
