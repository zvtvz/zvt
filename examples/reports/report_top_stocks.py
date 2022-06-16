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
        periods=[3, 8, 15],
        ignore_new_stock=True,
        ignore_st=True,
        adjust_type=None,
        top_count=20,
        turnover_threshold=0,
        turnover_rate_threshold=0,
        em_group="短期最强",
        em_group_over_write=True,
        return_type=TopType.positive,
    )

    report_top_entities(
        entity_type="stock",
        entity_provider="em",
        data_provider="em",
        periods=[30, 60],
        ignore_new_stock=True,
        ignore_st=True,
        adjust_type=None,
        top_count=20,
        turnover_threshold=0,
        turnover_rate_threshold=0,
        em_group="中期最强",
        em_group_over_write=True,
        return_type=TopType.positive,
    )

    report_top_entities(
        entity_type="stock",
        entity_provider="em",
        data_provider="em",
        periods=[365, 750],
        ignore_new_stock=True,
        ignore_st=True,
        adjust_type=None,
        top_count=25,
        turnover_threshold=100000000,
        turnover_rate_threshold=0.01,
        em_group="谁有我惨",
        em_group_over_write=True,
        return_type=TopType.negative,
    )


@sched.scheduled_job("cron", hour=17, minute=20, day_of_week="mon-fri")
def report_top_stockhk():
    report_top_entities(
        entity_type="stockhk",
        entity_provider="em",
        data_provider="em",
        top_count=10,
        periods=[3, 8, 15],
        ignore_new_stock=True,
        ignore_st=False,
        adjust_type=None,
        turnover_threshold=50000000,
        turnover_rate_threshold=0.005,
        em_group="短期最强",
        em_group_over_write=False,
        return_type=TopType.positive,
    )

    report_top_entities(
        entity_type="stockhk",
        entity_provider="em",
        data_provider="em",
        top_count=10,
        periods=[30, 60],
        ignore_new_stock=True,
        ignore_st=False,
        adjust_type=None,
        turnover_threshold=50000000,
        turnover_rate_threshold=0.005,
        em_group="中期最强",
        em_group_over_write=False,
        return_type=TopType.positive,
    )

    report_top_entities(
        entity_type="stockhk",
        entity_provider="em",
        data_provider="em",
        top_count=10,
        periods=[365, 750],
        ignore_new_stock=True,
        ignore_st=False,
        adjust_type=None,
        turnover_threshold=50000000,
        turnover_rate_threshold=0.005,
        em_group="谁有我惨",
        em_group_over_write=False,
        return_type=TopType.negative,
    )


if __name__ == "__main__":
    init_log("report_top_stocks.log")

    report_top_stocks()
    report_top_stockhk()

    sched.start()

    sched._thread.join()
