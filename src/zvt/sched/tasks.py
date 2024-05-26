# -*- coding: utf-8 -*-
from zvt.sched.sched import zvt_scheduler


@zvt_scheduler.scheduled_job("cron", hour=9, minute=25, day_of_week="mon-fri")
def record_stock_tick():
    pass
