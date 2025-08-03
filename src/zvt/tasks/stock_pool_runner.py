# -*- coding: utf-8 -*-
import logging

from apscheduler.schedulers.background import BackgroundScheduler

from zvt import zvt_config, init_log
from zvt.api.kdata import get_latest_kdata_date, get_kdata_schema
from zvt.api.selector import get_entity_ids_by_filter
from zvt.contract import AdjustType
from zvt.contract.api import get_entity_ids, get_data_count
from zvt.domain import (
    Stock,
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
from zvt.informer.informer import QiyeWechatBot
from zvt.tag.tag_stats import build_system_stock_pools, build_stock_pool_tag_stats
from zvt.utils.recorder_utils import run_data_recorder
from zvt.utils.time_utils import current_date

logger = logging.getLogger(__name__)

sched = BackgroundScheduler()

email_informer = EmailInformer()
bot = QiyeWechatBot()


def report_limit_up():
    latest_data = LimitUpInfo.query_data(order=LimitUpInfo.timestamp.desc(), limit=1, return_type="domain")
    timestamp = latest_data[0].timestamp
    df = LimitUpInfo.query_data(start_timestamp=timestamp, end_timestamp=timestamp, columns=["code", "name", "reason"])
    df["reason"] = df["reason"].str.split("+")
    print(df)
    email_informer.send_message(zvt_config["email_username"], f"{timestamp} 热门报告", f"{df}")


def record_stock_data(data_provider="em", entity_provider="em", sleeping_time=0, adjust_type=AdjustType.qfq):
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
        sleeping_time=0,
    )

    # 板块(概念，行业)
    run_data_recorder(domain=Block, entity_provider=entity_provider, data_provider=entity_provider, force_update=False)

    entity_ids = get_entity_ids(entity_schema=Block, filters=[Block.timestamp == None], provider=entity_provider)
    if entity_ids:
        # 板块行情(概念，行业)
        run_data_recorder(
            entity_ids=entity_ids,
            split_entity_ids_size=0,
            domain=Block1dKdata,
            entity_provider=entity_provider,
            data_provider=entity_provider,
            day_data=True,
            sleeping_time=0,
        )

    # 报告新概念和行业
    df = Block.query_data(
        filters=[Block.category == BlockCategory.concept.value],
        order=Block.list_date.desc(),
        index="entity_id",
        limit=7,
    )

    inform_email(
        entity_ids=df.index.tolist(),
        entity_type="block",
        target_date=current_date(),
        title="report 新概念",
        provider="em",
    )

    target_date = get_latest_kdata_date(entity_type="index", provider=data_provider)
    # A股标的
    run_data_recorder(domain=Stock, data_provider=data_provider, force_update=False)
    # A股行情
    normal_stock_ids = get_entity_ids_by_filter(entity_type="stock", provider="em", ignore_delist=True)

    kdata_schema = get_kdata_schema(entity_type="stock", level="1d", adjust_type=adjust_type)

    run_data_recorder(
        entity_ids=normal_stock_ids,
        split_entity_ids_size=0,
        domain=kdata_schema,
        data_provider=data_provider,
        entity_provider=entity_provider,
        day_data=True,
        sleeping_time=5,
        return_unfinished=True,
        end_timestamp=target_date,
    )


def record_stock_data_and_build_stock_pools(provider="em", adjust_type=AdjustType.qfq):
    # 获取 涨停 指数 板块(概念) 个股行情数据
    record_stock_data(data_provider=provider, adjust_type=adjust_type)

    kdata_date = get_latest_kdata_date(provider=provider, entity_type="stock", adjust_type=adjust_type)

    kdata_schema = get_kdata_schema(entity_type="stock", level="1d", adjust_type=adjust_type)
    kdata_size = get_data_count(kdata_schema, filters=[kdata_schema.timestamp == kdata_date], provider=provider)

    if kdata_size < 5000:
        logger.warning(f"当前行情数据量过少: {kdata_size}, 不进行股票池构建")
        email_informer.send_message(zvt_config["email_username"], f"{kdata_date} k线数据不完整", "k线数据不完整")
        bot.send_message(f"{kdata_date} k线数据不完整")
        return

    # 计算短期/中期最强 放量突破年线半年线个股
    compute_top_stocks(start_date=kdata_date, entity_type="stock", force_update=False, adjust_type=adjust_type)
    # 放入股票池
    build_system_stock_pools(start_date=kdata_date, entity_type="stock", force_update=False)
    for stock_pool_name in ["主线", "年线", "大局"]:
        build_stock_pool_tag_stats(stock_pool_name=stock_pool_name, entity_type="stock", force_rebuild_latest=True)

    bot.send_message(f"{kdata_date} 股票池构建完成")


if __name__ == "__main__":
    init_log("stock_pool_runner.log")
    record_stock_data_and_build_stock_pools()
    sched.add_job(
        func=record_stock_data_and_build_stock_pools, trigger="cron", hour=16, minute=00, day_of_week="mon-fri"
    )
    sched.start()
    sched._thread.join()
