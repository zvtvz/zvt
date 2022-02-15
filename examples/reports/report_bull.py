# -*- coding: utf-8 -*-
import logging

from apscheduler.schedulers.background import BackgroundScheduler

from examples.factors.tech_factor import BullAndUpFactor
from examples.report_utils import report_targets
from zvt import init_log
from zvt.contract import AdjustType

logger = logging.getLogger(__name__)

sched = BackgroundScheduler()


@sched.scheduled_job("cron", hour=19, minute=30, day_of_week="mon-fri")
def report_bull():
    report_targets(
        factor_cls=BullAndUpFactor,
        entity_provider="em",
        data_provider="em",
        title="bull股票",
        entity_type="stock",
        em_group="bull股票",
        em_group_over_write=True,
        filter_by_volume=False,
        adjust_type=AdjustType.hfq,
        start_timestamp="2019-01-01",
        turnover_threshold=400000000,
        turnover_rate_threshold=0.02,
    )
    report_targets(
        factor_cls=BullAndUpFactor,
        entity_provider="em",
        data_provider="em",
        title="bull板块",
        entity_type="block",
        em_group="强势板块",
        em_group_over_write=False,
        filter_by_volume=False,
        adjust_type=AdjustType.qfq,
        start_timestamp="2019-01-01",
        turnover_threshold=10000000000,
        turnover_rate_threshold=0.02,
    )


if __name__ == "__main__":
    init_log("report_bull.log")

    report_bull()

    sched.start()

    sched._thread.join()
