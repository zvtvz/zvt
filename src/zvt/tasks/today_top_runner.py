# -*- coding: utf-8 -*-
import logging
import time
from typing import List

import eastmoneypy
from apscheduler.schedulers.background import BackgroundScheduler

from zvt import init_log
from zvt.api.selector import get_top_up_today, get_top_down_today, get_top_vol
from zvt.domain import Stock
from zvt.informer.inform_utils import add_to_eastmoney
from zvt.recorders.em.em_api import record_hot_topic
from zvt.tag.common import InsertMode
from zvt.tag.tag_schemas import StockPools
from zvt.tag.tag_stats import build_stock_pool_and_tag_stats
from zvt.utils.time_utils import now_pd_timestamp, current_date

logger = logging.getLogger(__name__)


sched = BackgroundScheduler()


def calculate_top(clear_em=True):
    if clear_em:
        try:
            eastmoneypy.del_group("今日强势")
        except:
            pass

    seed = 0
    add_all_to_em = False
    while True:
        current_timestamp = now_pd_timestamp()

        if not Stock.in_trading_time():
            logger.info(f"calculate top finished at: {current_timestamp}")
            break

        if Stock.in_trading_time() and not Stock.in_real_trading_time():
            logger.info(f"Sleeping time......")
            time.sleep(60 * 1)
            continue

        if seed == 0:
            record_hot_topic()
            seed = seed + 1
            if seed == 5:
                seed = 0
        target_date = current_date()
        top_up_entity_ids = get_top_up_today()
        if top_up_entity_ids:
            build_stock_pool_and_tag_stats(
                entity_ids=top_up_entity_ids,
                stock_pool_name="今日强势",
                insert_mode=InsertMode.append,
                target_date=target_date,
                provider="qmt",
            )
            try:
                to_added = top_up_entity_ids
                if add_all_to_em:
                    stock_pools: List[StockPools] = StockPools.query_data(
                        filters=[StockPools.stock_pool_name == "今日强势"],
                        order=StockPools.timestamp.desc(),
                        limit=1,
                        return_type="domain",
                    )
                    if stock_pools:
                        to_added = stock_pools[0].entity_ids
                        if len(to_added) > 500:
                            to_added = get_top_vol(entity_ids=to_added, limit=500)

                add_to_eastmoney(
                    codes=[entity_id.split("_")[2] for entity_id in to_added], group="今日强势", over_write=False
                )
                add_all_to_em = False
            except Exception as e:
                logger.error(e)
                add_all_to_em = True

        top_down_entity_ids = get_top_down_today()
        if top_down_entity_ids:
            build_stock_pool_and_tag_stats(
                entity_ids=top_down_entity_ids,
                stock_pool_name="今日弱势",
                insert_mode=InsertMode.append,
                target_date=target_date,
                provider="qmt",
            )

        logger.info(f"Sleep 2 minutes to compute {target_date} top stock tag stats")
        time.sleep(60 * 2)


if __name__ == "__main__":
    init_log("today_top_runner.log")
    calculate_top(clear_em=False)
    sched.add_job(func=calculate_top, trigger="cron", hour=9, minute=26, day_of_week="mon-fri")
    sched.start()
    sched._thread.join()
