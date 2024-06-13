# -*- coding: utf-8 -*-
import logging

from apscheduler.schedulers.background import BackgroundScheduler

from examples.report_utils import report_top_entities, inform
from zvt import init_log
from zvt.api.stats import TopType, get_latest_kdata_date
from zvt.contract import AdjustType
from zvt.domain import Block, BlockCategory
from zvt.factors.top_stocks import get_top_stocks
from zvt.informer import EmailInformer

logger = logging.getLogger(__name__)

sched = BackgroundScheduler()

email_informer = EmailInformer()


@sched.scheduled_job("cron", hour=17, minute=0, day_of_week="mon-fri")
def report_top_stocks():
    # compute_top_stocks()
    provider = "em"
    entity_type = "stock"
    target_date = get_latest_kdata_date(provider=provider, entity_type=entity_type, adjust_type=AdjustType.hfq)
    selected = get_top_stocks(target_date=target_date, return_type="short")

    inform(
        email_informer,
        entity_ids=selected,
        target_date=target_date,
        title=f"stock 短期最强({len(selected)})",
        entity_provider=provider,
        entity_type=entity_type,
        em_group="短期最强",
        em_group_over_write=True,
        em_group_over_write_tag=True,
    )
    selected = get_top_stocks(target_date=target_date, return_type="long")

    inform(
        email_informer,
        entity_ids=selected,
        target_date=target_date,
        title=f"stock 中期最强({len(selected)})",
        entity_provider=provider,
        entity_type=entity_type,
        em_group="中期最强",
        em_group_over_write=True,
        em_group_over_write_tag=False,
    )

    # report_top_entities(
    #     entity_type="stock",
    #     entity_provider="em",
    #     data_provider="em",
    #     periods=[365, 750],
    #     ignore_new_stock=False,
    #     ignore_st=True,
    #     adjust_type=None,
    #     top_count=25,
    #     turnover_threshold=100000000,
    #     turnover_rate_threshold=0.01,
    #     informer=email_informer,
    #     em_group="谁有我惨",
    #     em_group_over_write=True,
    #     return_type=TopType.negative,
    # )


@sched.scheduled_job("cron", hour=17, minute=30, day_of_week="mon-fri")
def report_top_blocks():
    df = Block.query_data(filters=[Block.category == BlockCategory.industry.value], index="entity_id")

    entity_ids = df.index.tolist()
    report_top_entities(
        entity_type="block",
        entity_provider="em",
        data_provider="em",
        periods=[*range(2, 30)],
        ignore_new_stock=False,
        ignore_st=False,
        adjust_type=None,
        top_count=10,
        turnover_threshold=0,
        turnover_rate_threshold=0,
        informer=email_informer,
        em_group="最强行业",
        title="最强行业",
        em_group_over_write=True,
        return_type=TopType.positive,
        entity_ids=entity_ids,
    )

    df = Block.query_data(filters=[Block.category == BlockCategory.concept.value], index="entity_id")
    df = df[~df.name.str.contains("昨日")]
    entity_ids = df.index.tolist()
    report_top_entities(
        entity_type="block",
        entity_provider="em",
        data_provider="em",
        periods=[*range(2, 30)],
        ignore_new_stock=False,
        ignore_st=False,
        adjust_type=None,
        top_count=10,
        turnover_threshold=0,
        turnover_rate_threshold=0,
        informer=email_informer,
        em_group="最强概念",
        title="最强概念",
        em_group_over_write=True,
        return_type=TopType.positive,
        entity_ids=entity_ids,
    )


@sched.scheduled_job("cron", hour=17, minute=30, day_of_week="mon-fri")
def report_top_stockhks():
    report_top_entities(
        entity_type="stockhk",
        entity_provider="em",
        data_provider="em",
        top_count=10,
        periods=[*range(1, 15)],
        ignore_new_stock=False,
        ignore_st=False,
        adjust_type=None,
        turnover_threshold=30000000,
        turnover_rate_threshold=0.01,
        informer=email_informer,
        em_group="短期最强",
        title="短期最强",
        em_group_over_write=False,
        return_type=TopType.positive,
    )

    report_top_entities(
        entity_type="stockhk",
        entity_provider="em",
        data_provider="em",
        top_count=10,
        periods=[30, 50],
        ignore_new_stock=True,
        ignore_st=False,
        adjust_type=None,
        turnover_threshold=30000000,
        turnover_rate_threshold=0.01,
        informer=email_informer,
        em_group="中期最强",
        title="中期最强",
        em_group_over_write=False,
        return_type=TopType.positive,
    )

    # report_top_entities(
    #     entity_type="stockhk",
    #     entity_provider="em",
    #     data_provider="em",
    #     top_count=20,
    #     periods=[365, 750],
    #     ignore_new_stock=True,
    #     ignore_st=False,
    #     adjust_type=None,
    #     turnover_threshold=50000000,
    #     turnover_rate_threshold=0.005,
    #     informer=email_informer,
    #     em_group="谁有我惨",
    #     em_group_over_write=False,
    #     return_type=TopType.negative,
    # )


if __name__ == "__main__":
    init_log("report_tops.log")

    report_top_stocks()
    # report_top_blocks()
    report_top_stockhks()

    sched.start()

    sched._thread.join()
