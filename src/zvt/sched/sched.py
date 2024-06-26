# -*- coding: utf-8 -*-
import logging
import os

from apscheduler.executors.pool import ThreadPoolExecutor, ProcessPoolExecutor
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.schedulers.background import BackgroundScheduler

from zvt import ZVT_HOME

logger = logging.getLogger(__name__)

jobs_db_path = os.path.join(ZVT_HOME, "jobs.db")


jobstores = {"default": SQLAlchemyJobStore(url=f"sqlite:///{jobs_db_path}")}

executors = {"default": ThreadPoolExecutor(20), "processpool": ProcessPoolExecutor(5)}
job_defaults = {"coalesce": False, "max_instances": 1}

zvt_scheduler = BackgroundScheduler(jobstores=jobstores, executors=executors, job_defaults=job_defaults)


def sched_tasks():
    import platform

    if platform.system() == "Windows":
        try:
            from zvt.broker.qmt.qmt_quote import record_tick

            zvt_scheduler.add_job(func=record_tick, trigger="cron", hour=9, minute=19, day_of_week="mon-fri")
        except Exception as e:
            logger.error("QMT not work", e)
    else:
        logger.warning("QMT need run in Windows!")

    zvt_scheduler.start()


if __name__ == "__main__":
    sched_tasks()
