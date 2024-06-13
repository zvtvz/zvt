# -*- coding: utf-8 -*-
import logging

from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy import or_, and_

from examples.report_utils import inform
from zvt import init_log
from zvt.api.kdata import get_latest_kdata_date
from zvt.api.selector import get_big_players
from zvt.domain import (
    DragonAndTiger,
    Stock1dHfqKdata,
)
from zvt.informer import EmailInformer
from zvt.utils.recorder_utils import run_data_recorder
from zvt.utils.time_utils import date_time_by_interval, current_date, to_pd_timestamp

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

    email_action = EmailInformer()
    # recent year
    start_timestamp = date_time_by_interval(current_date(), -400)
    # 最近一年牛x的营业部
    players = get_big_players(start_timestamp=start_timestamp)

    # 最近30天有牛x的营业部上榜的个股
    recent_date = date_time_by_interval(current_date(), -30)
    selected = []
    for player in players:
        filters = [
            or_(
                and_(DragonAndTiger.dep1 == player, DragonAndTiger.dep1_rate >= 5),
                and_(DragonAndTiger.dep2 == player, DragonAndTiger.dep2_rate >= 5),
                and_(DragonAndTiger.dep3 == player, DragonAndTiger.dep3_rate >= 5),
                and_(DragonAndTiger.dep4 == player, DragonAndTiger.dep4_rate >= 5),
                and_(DragonAndTiger.dep5 == player, DragonAndTiger.dep5_rate >= 5),
            )
        ]
        df = DragonAndTiger.query_data(
            start_timestamp=recent_date,
            filters=filters,
            columns=[DragonAndTiger.timestamp, DragonAndTiger.entity_id, DragonAndTiger.code, DragonAndTiger.name],
            index="entity_id",
        )
        selected = selected + df.index.tolist()

    if selected:
        selected = list(set(selected))

    target_date = get_latest_kdata_date(provider=data_provider, entity_type="stock", adjust_type="hfq")
    df = Stock1dHfqKdata.query_data(
        provider=data_provider,
        entity_ids=selected,
        filters=[
            Stock1dHfqKdata.turnover_rate > 0.02,
            Stock1dHfqKdata.timestamp == to_pd_timestamp(target_date),
            Stock1dHfqKdata.turnover > 300000000,
        ],
        index=["entity_id"],
    )
    inform(
        action=email_action,
        entity_ids=df.index.tolist(),
        target_date=current_date(),
        title="report 龙虎榜",
        entity_provider=entity_provider,
        entity_type="stock",
        em_group="重要指数",
        em_group_over_write=False,
    )


if __name__ == "__main__":
    init_log("trading_runner.log")

    record_dragon_tiger()

    sched.start()

    sched._thread.join()
