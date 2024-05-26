# -*- coding: utf-8 -*-
import os

from apscheduler.executors.pool import ThreadPoolExecutor, ProcessPoolExecutor
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.schedulers.background import BackgroundScheduler

from zvt import ZVT_HOME

jobs_db_path = os.path.join(ZVT_HOME, "jobs.db")


jobstores = {"default": SQLAlchemyJobStore(url=f"sqlite:///{jobs_db_path}")}

executors = {"default": ThreadPoolExecutor(20), "processpool": ProcessPoolExecutor(5)}
job_defaults = {"coalesce": False, "max_instances": 3}

zvt_scheduler = BackgroundScheduler(jobstores=jobstores, executors=executors, job_defaults=job_defaults)
