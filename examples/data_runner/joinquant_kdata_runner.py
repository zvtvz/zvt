# -*- coding: utf-8 -*-
import logging

from apscheduler.schedulers.background import BackgroundScheduler

from zvt.domain import StockTradeDay

logger = logging.getLogger(__name__)

sched = BackgroundScheduler()

# -*- coding: utf-8 -*-
import logging

from apscheduler.schedulers.background import BackgroundScheduler

from examples.recorder_utils import run_data_recorder
from zvt import init_log
from zvt.domain import Stock, Stock1dHfqKdata

logger = logging.getLogger(__name__)

sched = BackgroundScheduler()


from jqdatapy import get_token
from zvt import zvt_config
get_token(zvt_config["jq_username"], zvt_config["jq_password"], force=True)


@sched.scheduled_job("cron", hour=15, minute=30)
def record_stock_data(data_provider="joinquant", entity_provider="joinquant"):
    # A股标的
    run_data_recorder(domain=Stock, data_provider=data_provider, force_update=False)
    # 交易日
    run_data_recorder(domain=StockTradeDay, data_provider=data_provider)
    # A股后复权行情
    run_data_recorder(
        domain=Stock1dHfqKdata,
        data_provider=data_provider,
        entity_provider=entity_provider,
        day_data=True,
        sleeping_time=0,
    )


if __name__ == "__main__":
    init_log("joinquant_kdata_runner.log")

    record_stock_data()

    sched.start()

    sched._thread.join()
