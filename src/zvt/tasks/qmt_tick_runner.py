# -*- coding: utf-8 -*-
from zvt import init_log
from zvt.broker.qmt.qmt_quote import record_tick

if __name__ == "__main__":
    init_log("qmt_tick_runner.log")
    from apscheduler.schedulers.background import BackgroundScheduler

    sched = BackgroundScheduler()
    record_tick()
    sched.add_job(func=record_tick, trigger="cron", hour=9, minute=18, day_of_week="mon-fri")
    sched.start()
    sched._thread.join()
