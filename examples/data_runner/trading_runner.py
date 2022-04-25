# -*- coding: utf-8 -*-
import logging

from apscheduler.schedulers.background import BackgroundScheduler

from examples.recorder_utils import run_data_recorder
from zvt import init_log
from zvt.domain import (
    DragonAndTiger,
)

logger = logging.getLogger(__name__)

sched = BackgroundScheduler()


@sched.scheduled_job("cron", hour=18, minute=00, day_of_week="mon-fri")
def record_dragon_tiger(data_provider="em", entity_provider="em", sleeping_time=2):
    # 龙虎榜数据
    run_data_recorder(
        domain=DragonAndTiger,
        data_provider=data_provider,
        entity_provider=entity_provider,
        day_data=True,
        sleeping_time=sleeping_time,
    )


if __name__ == "__main__":
    init_log("trading_runner.log")

    record_dragon_tiger()

    sched.start()

    sched._thread.join()
