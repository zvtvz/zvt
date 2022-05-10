# -*- coding: utf-8 -*-
import logging

from apscheduler.schedulers.background import BackgroundScheduler

from examples.report_utils import report_targets
from zvt import init_log
from zvt.api.kdata import get_latest_kdata_date
from zvt.contract import AdjustType
from zvt.domain import Stock1dHfqKdata
from zvt.factors import VolumeUpMaFactor
from zvt.utils import to_pd_timestamp

logger = logging.getLogger(__name__)

sched = BackgroundScheduler()


def get_by_cap(
    timestamp,
    cap_start=4000000000,
    cap_end=15000000000,
    provider="em",
):
    df = Stock1dHfqKdata.query_data(
        provider=provider,
        filters=[Stock1dHfqKdata.timestamp == to_pd_timestamp(timestamp)],
        index="entity_id",
    )
    df["cap"] = df["turnover"] / df["turnover_rate"]
    return df.loc[(df["cap"] >= cap_start) & (df["cap"] <= cap_end)].index.tolist()


@sched.scheduled_job("cron", hour=17, minute=0, day_of_week="mon-fri")
def report_vol_up():
    report_targets(
        factor_cls=VolumeUpMaFactor,
        entity_provider="em",
        data_provider="em",
        em_group="年线股票",
        title="放量突破(半)年线股票",
        entity_type="stock",
        em_group_over_write=True,
        filter_by_volume=False,
        adjust_type=AdjustType.hfq,
        start_timestamp="2019-01-01",
        # factor args
        windows=[120, 250],
        over_mode="or",
        up_intervals=40,
        turnover_threshold=300000000,
        turnover_rate_threshold=0.02,
    )

    target_date = get_latest_kdata_date(entity_type="stock", adjust_type=AdjustType.hfq, provider="em")

    entity_ids = get_by_cap(timestamp=target_date)
    report_targets(
        factor_cls=VolumeUpMaFactor,
        entity_provider="em",
        data_provider="em",
        em_group="强势板块",
        title="小市值年线股票",
        entity_type="stock",
        em_group_over_write=True,
        filter_by_volume=False,
        adjust_type=AdjustType.hfq,
        start_timestamp="2019-01-01",
        # factor args
        windows=[120, 250],
        over_mode="or",
        up_intervals=120,
        turnover_threshold=100000000,
        turnover_rate_threshold=0.02,
        entity_ids=entity_ids,
    )

    report_targets(
        factor_cls=VolumeUpMaFactor,
        entity_provider="em",
        data_provider="em",
        em_group="强势板块",
        title="放量突破(半)年线板块",
        entity_type="block",
        em_group_over_write=False,
        filter_by_volume=False,
        adjust_type=AdjustType.qfq,
        start_timestamp="2019-01-01",
        # factor args
        windows=[120, 250],
        over_mode="or",
        up_intervals=40,
        turnover_threshold=10000000000,
        turnover_rate_threshold=0.02,
    )

    report_targets(
        factor_cls=VolumeUpMaFactor,
        entity_provider="em",
        data_provider="em",
        em_group="年线股票",
        title="放量突破(半)年线港股",
        entity_type="stockhk",
        em_group_over_write=False,
        filter_by_volume=False,
        adjust_type=AdjustType.hfq,
        start_timestamp="2019-01-01",
        # factor args
        windows=[120, 250],
        over_mode="or",
        up_intervals=20,
        turnover_threshold=100000000,
        turnover_rate_threshold=0.02,
    )


if __name__ == "__main__":
    init_log("report_vol_up.log")

    report_vol_up()

    sched.start()

    sched._thread.join()
