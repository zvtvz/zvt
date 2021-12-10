# -*- coding: utf-8 -*-
import logging

from apscheduler.schedulers.background import BackgroundScheduler

from examples.recorder_utils import run_data_recorder
from examples.utils import add_to_eastmoney
from zvt import init_log, zvt_config
from zvt.domain import Stock, Stock1dHfqKdata, Stockhk, Stockhk1dHfqKdata, Block, Block1dKdata, BlockCategory
from zvt.informer import EmailInformer
from zvt.utils import next_date, current_date

logger = logging.getLogger(__name__)

sched = BackgroundScheduler()


@sched.scheduled_job("cron", hour=15, minute=30)
def record_stock_data(data_provider="em", entity_provider="em", sleeping_time=2):
    # A股标的
    run_data_recorder(domain=Stock, data_provider=data_provider, force_update=False)
    # A股后复权行情
    run_data_recorder(
        domain=Stock1dHfqKdata,
        data_provider=data_provider,
        entity_provider=entity_provider,
        day_data=True,
        sleeping_time=sleeping_time,
    )

    # 板块(概念，行业)
    run_data_recorder(domain=Block, data_provider="eastmoney", force_update=False)
    # 板块行情(概念，行业)
    run_data_recorder(domain=Block1dKdata, data_provider="em", day_data=True, sleeping_time=sleeping_time)

    # 报告新概念和行业
    email_action = EmailInformer()
    list_date = next_date(current_date(), -90)
    df = Block.query_data(
        filters=[Block.category == BlockCategory.concept.value, Block.list_date >= list_date], index="entity_id"
    )

    # add them to eastmoney
    try:
        add_to_eastmoney(codes=df["code"], entity_type="block", group="新概念", over_write=False)
    except Exception as e:
        email_action.send_message(
            zvt_config["email_username"], f"report_concept error", "report_concept error:{}".format(e)
        )


@sched.scheduled_job("cron", hour=16, minute=30)
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
