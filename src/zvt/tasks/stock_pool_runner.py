# -*- coding: utf-8 -*-
import logging

from apscheduler.schedulers.background import BackgroundScheduler

from zvt import zvt_config, init_log
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
    LimitUpInfo,
)
from zvt.factors import compute_top_stocks
from zvt.informer import EmailInformer
from zvt.informer.inform_utils import inform_email
from zvt.tag.tag_stats import build_system_stock_pools, build_stock_pool_tag_stats
from zvt.utils.recorder_utils import run_data_recorder
from zvt.utils.time_utils import current_date

logger = logging.getLogger(__name__)

sched = BackgroundScheduler()

email_informer = EmailInformer()


def report_limit_up():
    latest_data = LimitUpInfo.query_data(order=LimitUpInfo.timestamp.desc(), limit=1, return_type="domain")
    timestamp = latest_data[0].timestamp
    df = LimitUpInfo.query_data(start_timestamp=timestamp, end_timestamp=timestamp, columns=["code", "name", "reason"])
    df["reason"] = df["reason"].str.split("+")
    print(df)
    email_informer.send_message(zvt_config["email_username"], f"{timestamp} 热门报告", f"{df}")


def record_stock_data(data_provider="em", entity_provider="em", sleeping_time=0):
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

    # 报告新概念和行业
    df = Block.query_data(
        filters=[Block.category == BlockCategory.concept.value],
        order=Block.list_date.desc(),
        index="entity_id",
        limit=7,
    )

    inform_email(
        entity_ids=df.index.tolist(), entity_type="block", target_date=current_date(), title="report 新概念", provider="em"
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


def record_data_and_build_stock_pools():
    # 获取 涨停 指数 板块(概念) 个股行情数据
    record_stock_data()

    # 计算短期/中期最强 放量突破年线半年线个股
    compute_top_stocks()
    # 放入股票池
    build_system_stock_pools()
    for stock_pool_name in ["main_line", "vol_up", "大局"]:
        build_stock_pool_tag_stats(stock_pool_name=stock_pool_name, force_rebuild_latest=True)


if __name__ == "__main__":
    init_log("sotck_pool_runner.log")
    record_data_and_build_stock_pools()
    sched.add_job(func=record_data_and_build_stock_pools, trigger="cron", hour=16, minute=00, day_of_week="mon-fri")
    sched.start()
    sched._thread.join()
