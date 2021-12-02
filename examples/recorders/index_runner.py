# -*- coding: utf-8 -*-
import logging
import time

from apscheduler.schedulers.background import BackgroundScheduler

from zvt import init_log, zvt_config
from zvt.consts import IMPORTANT_INDEX
from zvt.domain import Index, Index1dKdata, IndexStock
from zvt.informer.informer import EmailInformer

logger = logging.getLogger(__name__)

sched = BackgroundScheduler()


# 自行更改定定时运行时间
@sched.scheduled_job("cron", hour=1, minute=00, day_of_week=5)
def record_index():
    while True:
        email_action = EmailInformer()

        try:
            Index.record_data(provider="exchange")

            # 默认只抓取 国证1000 国证2000 国证成长 国证价值 的组成个股
            index_ids = ["index_sz_399311", "index_sz_399303", "index_sz_399370", "index_sz_399371"]
            IndexStock.record_data(provider="exchange", entity_ids=index_ids)

            email_action.send_message(zvt_config["email_username"], "record index finished", "")
            break
        except Exception as e:
            msg = f"record index error:{e}"
            logger.exception(msg)

            email_action.send_message(zvt_config["email_username"], "record index error", msg)
            time.sleep(60)


@sched.scheduled_job("cron", hour=16, minute=20)
def record_index_kdata():
    while True:
        email_action = EmailInformer()

        try:
            # 指数k线
            Index1dKdata.record_data(provider="em", codes=IMPORTANT_INDEX)
            email_action.send_message(zvt_config["email_username"], "record index kdata finished", "")
            break
        except Exception as e:
            msg = f"record index kdata error:{e}"
            logger.exception(msg)

            email_action.send_message(zvt_config["email_username"], "record index kdata error", msg)
            time.sleep(60)


if __name__ == "__main__":
    init_log("index_runner.log")

    record_index_kdata()

    sched.start()

    sched._thread.join()
