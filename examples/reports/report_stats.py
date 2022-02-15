# -*- coding: utf-8 -*-
import logging

from apscheduler.schedulers.background import BackgroundScheduler

from examples.report_utils import report_top_stats
from zvt import init_log

logger = logging.getLogger(__name__)

sched = BackgroundScheduler()


@sched.scheduled_job("cron", hour=19, minute=30, day_of_week="mon-fri")
def report_stats():
    report_top_stats(
        entity_type="stock",
        entity_provider="em",
        data_provider="em",
        periods=[7, 30, 365],
        ignore_new_stock=True,
        adjust_type=None,
        top_count=30,
        turnover_threshold=100000000,
        turnover_rate_threshold=0.02,
        em_group_over_write=True,
    )
    report_top_stats(
        entity_type="stockhk",
        entity_provider="em",
        data_provider="em",
        top_count=30,
        periods=[7, 30, 365],
        ignore_new_stock=True,
        adjust_type=None,
        turnover_threshold=100000000,
        turnover_rate_threshold=0.005,
        em_group_over_write=False,
    )


if __name__ == "__main__":
    init_log("report_stats.log")

    report_stats()

    sched.start()

    sched._thread.join()
