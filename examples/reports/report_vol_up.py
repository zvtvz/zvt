# -*- coding: utf-8 -*-
import logging

from zvt.factors.ma import VolumeUpMaFactor
from apscheduler.schedulers.background import BackgroundScheduler

from examples.report_utils import report_targets, inform
from zvt import init_log
from zvt.api.kdata import get_latest_kdata_date
from zvt.contract import AdjustType
from zvt.factors.top_stocks import get_top_stocks
from zvt.informer import EmailInformer

logger = logging.getLogger(__name__)

sched = BackgroundScheduler()

email_informer = EmailInformer()


@sched.scheduled_job("cron", hour=17, minute=0, day_of_week="mon-fri")
def report_vol_up_stocks():
    provider = "em"
    entity_type = "stock"
    target_date = get_latest_kdata_date(provider=provider, entity_type=entity_type, adjust_type=AdjustType.hfq)
    selected = get_top_stocks(target_date=target_date, return_type="small_vol_up")

    inform(
        email_informer,
        entity_ids=selected,
        target_date=target_date,
        title=f"stock 放量突破(半)年线小市值股票({len(selected)})",
        entity_provider=provider,
        entity_type=entity_type,
        em_group="年线股票",
        em_group_over_write=True,
        em_group_over_write_tag=False,
    )
    selected = get_top_stocks(target_date=target_date, return_type="big_vol_up")

    inform(
        email_informer,
        entity_ids=selected,
        target_date=target_date,
        title=f"stock 放量突破(半)年线大市值股票({len(selected)})",
        entity_provider=provider,
        entity_type=entity_type,
        em_group="年线股票",
        em_group_over_write=False,
        em_group_over_write_tag=False,
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
