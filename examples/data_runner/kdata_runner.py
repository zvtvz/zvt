# -*- coding: utf-8 -*-
import logging

from apscheduler.schedulers.background import BackgroundScheduler

from examples.report_utils import inform
from examples.utils import get_hot_topics
from zvt import init_log, zvt_config
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
    LimitUpInfo,
)
from zvt.informer import EmailInformer
from zvt.utils.time_utils import current_date
from zvt.utils.recorder_utils import run_data_recorder

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


def report_limit_up():
    latest_data = LimitUpInfo.query_data(order=LimitUpInfo.timestamp.desc(), limit=1, return_type="domain")
    timestamp = latest_data[0].timestamp
    df = LimitUpInfo.query_data(start_timestamp=timestamp, end_timestamp=timestamp, columns=["code", "name", "reason"])
    df["reason"] = df["reason"].str.split("+")
    print(df)
    EmailInformer().send_message(zvt_config["email_username"], f"{timestamp} 热门报告", f"{df}")


def report_hot_topics():
    topics_long = get_hot_topics(days_ago=20)
    topics_short = get_hot_topics(days_ago=5)

    set1 = set(topics_long.keys())
    set2 = set(topics_short.keys())

    same = set1 & set2
    print(same)

    old_topics = set1 - set2
    print(old_topics)
    new_topics = set2 - set1
    print(new_topics)

    msg = f"""
  一直热门:{same}
  ---:{old_topics}
  +++:{new_topics}

  长期统计:{topics_long}
  短期统计:{topics_short}
    """

    print(msg)
    EmailInformer().send_message(zvt_config["email_username"], f"{current_date()} 热门报告", msg)


@sched.scheduled_job("cron", hour=15, minute=30, day_of_week="mon-fri")
def record_stock_data(data_provider="em", entity_provider="em", sleeping_time=0):
    email_action = EmailInformer()
    # 涨停数据
    run_data_recorder(domain=LimitUpInfo, data_provider=None, force_update=False)
    report_limit_up()

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
    # run_data_recorder(
    #     domain=BlockStock,
    #     entity_provider=entity_provider,
    #     data_provider=entity_provider,
    #     sleeping_time=sleeping_time,
    # )

    # 报告新概念和行业
    df = Block.query_data(
        filters=[Block.category == BlockCategory.concept.value],
        order=Block.list_date.desc(),
        index="entity_id",
        limit=7,
    )

    inform(
        action=email_action,
        entity_ids=df.index.tolist(),
        target_date=current_date(),
        title="report 新概念",
        entity_provider=entity_provider,
        entity_type="block",
        em_group=None,
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
        return_unfinished=True,
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
