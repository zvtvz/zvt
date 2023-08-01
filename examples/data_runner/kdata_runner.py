# -*- coding: utf-8 -*-
import logging

from apscheduler.schedulers.background import BackgroundScheduler

from examples.recorder_utils import run_data_recorder
from examples.report_utils import inform
from zvt import init_log
from zvt.api.selector import get_entity_ids_by_filter
from zvt.domain import (
    Stock,
    Stock1dHfqKdata,
    Stockhk,
    Stockhk1dHfqKdata,
    Block,
    Block1dKdata,
    BlockCategory,
    Index,
    Index1dKdata,
    StockNews,
)
from zvt.informer import EmailInformer
from zvt.utils import next_date, current_date

logger = logging.getLogger(__name__)

sched = BackgroundScheduler()


@sched.scheduled_job("cron", hour=16, minute=30, day_of_week="mon-fri")
def record_stock_news(data_provider="em"):
    normal_stock_ids = get_entity_ids_by_filter(
        provider="em", ignore_delist=True, ignore_st=False, ignore_new_stock=False
    )

    run_data_recorder(
        entity_ids=normal_stock_ids,
        day_data=True,
        domain=StockNews,
        data_provider=data_provider,
        force_update=False,
        sleeping_time=2,
    )


@sched.scheduled_job("cron", hour=15, minute=30, day_of_week="mon-fri")
def record_stock_data(data_provider="em", entity_provider="em", sleeping_time=2):
    # A股指数
    run_data_recorder(domain=Index, data_provider=data_provider, force_update=False)
    # A股指数行情
    run_data_recorder(
        domain=Index1dKdata,
        data_provider=data_provider,
        entity_provider=entity_provider,
        day_data=True,
        sleeping_time=sleeping_time,
    )

    # 板块(概念，行业)
    run_data_recorder(domain=Block, entity_provider=entity_provider, data_provider=entity_provider, force_update=False)
    # 板块行情(概念，行业)
    run_data_recorder(
        domain=Block1dKdata,
        entity_provider=entity_provider,
        data_provider=entity_provider,
        day_data=True,
        sleeping_time=sleeping_time,
    )

    # 报告新概念和行业
    email_action = EmailInformer()
    df = Block.query_data(
        filters=[Block.category == BlockCategory.concept.value],
        order=Block.list_date.desc(),
        index="entity_id",
        limit=5,
    )

    inform(
        action=email_action,
        entity_ids=df.index.tolist(),
        target_date=current_date(),
        title="report 新概念",
        entity_provider=entity_provider,
        entity_type="block",
        em_group="练气",
        em_group_over_write=False,
    )

    # A股标的
    run_data_recorder(domain=Stock, data_provider=data_provider, force_update=False)
    # A股后复权行情
    normal_stock_ids = get_entity_ids_by_filter(
        provider="em", ignore_delist=True, ignore_st=False, ignore_new_stock=False
    )

    run_data_recorder(
        entity_ids=normal_stock_ids,
        domain=Stock1dHfqKdata,
        data_provider=data_provider,
        entity_provider=entity_provider,
        day_data=True,
        sleeping_time=sleeping_time,
    )


@sched.scheduled_job("cron", hour=16, minute=30, day_of_week="mon-fri")
def record_stockhk_data(data_provider="em", entity_provider="em", sleeping_time=2):
    # 港股标的
    run_data_recorder(domain=Stockhk, data_provider=data_provider, force_update=False)
    # 港股后复权行情
    df = Stockhk.query_data(filters=[Stockhk.south == True], index="entity_id")
    run_data_recorder(
        domain=Stockhk1dHfqKdata,
        entity_ids=df.index.tolist(),
        data_provider=data_provider,
        entity_provider=entity_provider,
        day_data=True,
        sleeping_time=sleeping_time,
    )


if __name__ == "__main__":
    init_log("kdata_runner.log")

    record_stock_data()
    record_stockhk_data()

    sched.start()

    sched._thread.join()
