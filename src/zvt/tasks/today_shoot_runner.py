# -*- coding: utf-8 -*-
import logging
import time
from typing import List

from apscheduler.schedulers.background import BackgroundScheduler

from zvt import init_log
from zvt.api.selector import get_shoot_today
from zvt.domain import Stock
from zvt.informer.inform_utils import add_to_eastmoney
from zvt.tag.common import InsertMode
from zvt.tag.tag_schemas import StockPools
from zvt.tag.tag_stats import refresh_stock_pool
from zvt.utils.time_utils import (
    now_pd_timestamp,
    current_date,
)

logger = logging.getLogger(__name__)

sched = BackgroundScheduler()


def calculate_shoot():
    first_time = True
    stock_pool_name = "今日异动"
    while True:
        if not first_time and Stock.in_trading_time() and not Stock.in_real_trading_time():
            logger.info(f"Sleeping time......")
            time.sleep(30 * 1)
            continue

        try:
            shoot_up, shoot_down = get_shoot_today()

            if len(shoot_up) > 80:
                logger.warning(f"shoot_up count size: {len(shoot_up)}")
                shoot_up = shoot_up[:80]

            if shoot_up:
                over_write = False
                stock_pools: List[StockPools] = StockPools.query_data(
                    filters=[StockPools.stock_pool_name == stock_pool_name],
                    order=StockPools.timestamp.desc(),
                    limit=1,
                    return_type="domain",
                )
                if stock_pools and (len(stock_pools[0].entity_ids) > 80):
                    over_write = True

                refresh_stock_pool(
                    entity_ids=shoot_up,
                    stock_pool_name=stock_pool_name,
                    insert_mode=InsertMode.overwrite if over_write else InsertMode.append,
                    target_date=current_date(),
                )
                add_to_eastmoney(
                    codes=[entity_id.split("_")[2] for entity_id in shoot_up],
                    group=stock_pool_name,
                    over_write=over_write,
                )
        except Exception as e:
            logger.error("Failed to handle shoot today", exc_info=True)

        first_time = False

        if not Stock.in_trading_time():
            current_timestamp = now_pd_timestamp()
            logger.info(f"calculate shoot finished at: {current_timestamp}")
            break

        logger.info(f"Sleep 10 seconds")
        time.sleep(10)


if __name__ == "__main__":
    init_log("today_shoot_runner.log")
    calculate_shoot()
    sched.add_job(func=calculate_shoot, trigger="cron", hour=9, minute=50, day_of_week="mon-fri")
    sched.start()
    sched._thread.join()
