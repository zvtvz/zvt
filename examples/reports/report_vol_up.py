# -*- coding: utf-8 -*-
import logging

from apscheduler.schedulers.background import BackgroundScheduler

from examples.report_utils import report_targets
from zvt import init_log
from zvt.api.kdata import get_latest_kdata_date
from zvt.api.selector import get_mini_and_small_stock, get_middle_and_big_stock
from zvt.contract import AdjustType
from zvt.factors import VolumeUpMaFactor
from zvt.informer import EmailInformer

logger = logging.getLogger(__name__)

sched = BackgroundScheduler()

email_informer = EmailInformer()


@sched.scheduled_job("cron", hour=17, minute=0, day_of_week="mon-fri")
def report_vol_up_stocks():
    target_date = get_latest_kdata_date(entity_type="stock", adjust_type=AdjustType.hfq, provider="em")
    entity_ids = get_mini_and_small_stock(timestamp=target_date, provider="em")

    report_targets(
        factor_cls=VolumeUpMaFactor,
        entity_provider="em",
        data_provider="em",
        informer=email_informer,
        em_group="年线股票",
        title="放量突破(半)年线小市值股票",
        entity_type="stock",
        em_group_over_write=True,
        filter_by_volume=False,
        adjust_type=AdjustType.hfq,
        start_timestamp="2021-01-01",
        # factor args
        windows=[120, 250],
        over_mode="or",
        up_intervals=60,
        turnover_threshold=300000000,
        turnover_rate_threshold=0.02,
        entity_ids=entity_ids,
    )

    entity_ids = get_middle_and_big_stock(timestamp=target_date)
    report_targets(
        factor_cls=VolumeUpMaFactor,
        entity_provider="em",
        data_provider="em",
        informer=email_informer,
        em_group="年线股票",
        title="放量突破(半)年线大市值股票",
        entity_type="stock",
        em_group_over_write=False,
        filter_by_volume=False,
        adjust_type=AdjustType.hfq,
        start_timestamp="2021-01-01",
        # factor args
        windows=[120, 250],
        over_mode="or",
        up_intervals=60,
        turnover_threshold=300000000,
        turnover_rate_threshold=0.01,
        entity_ids=entity_ids,
    )


@sched.scheduled_job("cron", hour=17, minute=30, day_of_week="mon-fri")
def report_vol_up_stockhks():
    report_targets(
        factor_cls=VolumeUpMaFactor,
        entity_provider="em",
        data_provider="em",
        informer=email_informer,
        em_group="年线股票",
        title="放量突破(半)年线港股",
        entity_type="stockhk",
        em_group_over_write=False,
        filter_by_volume=False,
        adjust_type=AdjustType.hfq,
        start_timestamp="2021-01-01",
        # factor args
        windows=[120, 250],
        over_mode="or",
        up_intervals=60,
        turnover_threshold=100000000,
        turnover_rate_threshold=0.01,
    )


if __name__ == "__main__":
    init_log("report_vol_up.log")

    report_vol_up_stocks()
    report_vol_up_stockhks()
    sched.start()

    sched._thread.join()
