# -*- coding: utf-8 -*-
from zvt.broker.qmt.qmt_quote import record_tick

if __name__ == "__main__":
    from apscheduler.schedulers.background import BackgroundScheduler

    sched = BackgroundScheduler()
    record_tick()
    sched.add_job(func=record_tick, trigger="cron", hour=9, minute=18, day_of_week="mon-fri")
    sched.start()
    sched._thread.join()
