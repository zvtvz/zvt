# -*- coding: utf-8 -*-
import logging

from apscheduler.schedulers.background import BackgroundScheduler

from examples.recorder_utils import run_data_recorder
from zvt import init_log
from zvt.domain import Fund, FundStock, StockValuation

logger = logging.getLogger(__name__)

sched = BackgroundScheduler()


from jqdatapy import get_token
from zvt import zvt_config
get_token(zvt_config["jq_username"], zvt_config["jq_password"], force=True)

# 周6抓取
@sched.scheduled_job("cron", hour=10, minute=00, day_of_week=5)
def record_fund_data(data_provider="joinquant", entity_provider="joinquant"):
    # 基金
    run_data_recorder(domain=Fund, data_provider=data_provider, sleeping_time=0)
    # 基金持仓
    run_data_recorder(domain=FundStock, data_provider=data_provider, entity_provider=entity_provider, sleeping_time=0)
    # 个股估值
    run_data_recorder(
        domain=StockValuation,
        data_provider=data_provider,
        entity_provider=entity_provider,
        sleeping_time=0,
        day_data=True,
    )





if __name__ == "__main__":
    init_log("joinquant_fund_runner.log")

    record_fund_data()

    sched.start()

    sched._thread.join()
