# -*- coding: utf-8 -*-
import logging
import time
from typing import Type

from tabulate import tabulate

from examples.utils import add_to_eastmoney
from zvt import zvt_config
from zvt.api import get_top_volume_entities, get_top_performance_entities
from zvt.api.kdata import get_latest_kdata_date, get_kdata_schema, default_adjust_type
from zvt.contract import AdjustType
from zvt.contract.api import get_entities, get_entity_schema, get_entity_ids, decode_entity_id
from zvt.contract.factor import Factor
from zvt.factors import TargetSelector, SelectMode
from zvt.informer import EmailInformer
from zvt.utils import next_date

logger = logging.getLogger("__name__")


def report_targets(
    factor_cls: Type[Factor],
    entity_provider,
    data_provider,
    title,
    entity_type="stock",
    em_group=None,
    em_group_over_write=True,
    filter_by_volume=True,
    adjust_type=None,
    start_timestamp="2019-01-01",
    **factor_kv,
):
    logger.info(
        f"entity_provider: {entity_provider}, data_provider: {data_provider}, entity_type: {entity_type}, start_timestamp: {start_timestamp}"
    )
    error_count = 0

    while error_count <= 10:
        email_action = EmailInformer()

        try:
            if entity_type == "stock" and not adjust_type:
                adjust_type = AdjustType.hfq

            target_date = get_latest_kdata_date(entity_type=entity_type, adjust_type=adjust_type)
            logger.info(f"target_date :{target_date}")

            current_entity_pool = None
            if filter_by_volume:
                # 成交量
                vol_df = get_top_volume_entities(
                    entity_type=entity_type,
                    start_timestamp=next_date(target_date, -30),
                    end_timestamp=target_date,
                    adjust_type=adjust_type,
                    pct=0.4,
                )
                current_entity_pool = vol_df.index.tolist()
                logger.info(f"current_entity_pool({len(current_entity_pool)}): {current_entity_pool}")

            # add the factor
            my_selector = TargetSelector(
                start_timestamp=start_timestamp, end_timestamp=target_date, select_mode=SelectMode.condition_or
            )
            entity_schema = get_entity_schema(entity_type=entity_type)
            tech_factor = factor_cls(
                entity_schema=entity_schema,
                entity_provider=entity_provider,
                provider=data_provider,
                entity_ids=current_entity_pool,
                start_timestamp=start_timestamp,
                end_timestamp=target_date,
                adjust_type=adjust_type,
                **factor_kv,
            )
            my_selector.add_factor(tech_factor)

            my_selector.run()

            long_stocks = my_selector.get_open_long_targets(timestamp=target_date)

            msg = "no targets"

            if long_stocks:
                entities = get_entities(
                    provider=entity_provider, entity_type=entity_type, entity_ids=long_stocks, return_type="domain"
                )
                if em_group:
                    try:
                        codes = [entity.code for entity in entities]
                        add_to_eastmoney(
                            codes=codes, entity_type=entity_type, group=em_group, over_write=em_group_over_write
                        )
                    except Exception as e:
                        email_action.send_message(
                            zvt_config["email_username"],
                            f"report {entity_type}{factor_cls.__name__} error",
                            f"report {entity_type}{factor_cls.__name__} error: {e}",
                        )

                infos = [f"{entity.name}({entity.code})" for entity in entities]
                msg = "\n".join(infos) + "\n"

            logger.info(msg)

            email_action.send_message(zvt_config["email_username"], f"{target_date} {title}", msg)

            break
        except Exception as e:
            logger.exception("report error:{}".format(e))
            time.sleep(60 * 3)
            error_count = error_count + 1
            if error_count == 10:
                email_action.send_message(
                    zvt_config["email_username"],
                    f"report {entity_type}{factor_cls.__name__} error",
                    f"report {entity_type}{factor_cls.__name__} error: {e}",
                )


def report_top_stats(
    entity_provider,
    data_provider,
    periods=[7, 30, 180, 365],
    ignore_new_stock=True,
    entity_type="stock",
    adjust_type=None,
    top_count=30,
):
    if not adjust_type:
        adjust_type = default_adjust_type(entity_type=entity_type)
    kdata_schema = get_kdata_schema(entity_type=entity_type, adjust_type=adjust_type)
    entity_schema = get_entity_schema(entity_type=entity_type)
    latest_day = kdata_schema.query_data(
        provider=data_provider, order=kdata_schema.timestamp.desc(), limit=1, return_type="domain"
    )
    current_timestamp = latest_day[0].timestamp
    email_action = EmailInformer()

    # 至少上市一年
    filters = None
    if ignore_new_stock:
        pre_year = next_date(current_timestamp, -365)

        entity_ids = get_entity_ids(
            provider=entity_provider, entity_schema=entity_schema, filters=[entity_schema.timestamp <= pre_year]
        )
        filters = [kdata_schema.entity_id.in_(entity_ids)]

    stats = []
    ups = []
    downs = []

    for period in periods:
        start = next_date(current_timestamp, -period)
        df, _ = get_top_performance_entities(
            entity_type=entity_type,
            start_timestamp=start,
            filters=filters,
            pct=1,
            show_name=True,
            entity_provider=entity_provider,
            data_provider=data_provider,
        )
        df.rename(columns={"score": f"score_{period}"}, inplace=True)
        ups.append(tabulate(df.iloc[:top_count], headers="keys"))
        downs.append(tabulate(df.iloc[-top_count:], headers="keys"))

        stats.append(tabulate(df.describe(), headers="keys"))

        # 最近一个月和一周最靓仔的
        if period == 7 or period == 30:
            # add them to eastmoney
            try:
                codes = [decode_entity_id(entity_id)[2] for entity_id in df.index[:top_count]]
                add_to_eastmoney(codes=codes, entity_type=entity_type, group="最靓仔", over_write=False)
            except Exception as e:
                logger.exception(e)
                email_action.send_message(
                    zvt_config["email_username"], f"report_top_stats error", "report_top_stats error:{}".format(e)
                )

        # 一年内没怎么动的
        if period == 365 and False:
            stable_df = df[(df["score_365"] > -0.1) & (df["score_365"] < 0.1)]
            vol_df = get_top_volume_entities(
                entity_type=entity_type,
                entity_ids=stable_df.index.tolist(),
                start_timestamp=start,
                data_provider=data_provider,
            )

            # add them to eastmoney
            try:
                codes = [decode_entity_id(entity_id)[2] for entity_id in vol_df.index[:top_count]]
                add_to_eastmoney(codes=codes, entity_type="stock", group="躺尸一年")
            except Exception as e:
                logger.exception(e)
                email_action.send_message(
                    zvt_config["email_username"], f"report_top_stats error", "report_top_stats error:{}".format(e)
                )

    msg = "\n"
    for s in stats:
        msg = msg + s + "\n"
    email_action.send_message(zvt_config["email_username"], f"{current_timestamp} {entity_type}统计报告", msg)

    msg = "\n"
    for up in ups:
        msg = msg + up + "\n"
    email_action.send_message(zvt_config["email_username"], f"{current_timestamp} {entity_type}涨幅统计报告", msg)

    msg = "\n"
    for down in downs:
        msg = msg + down + "\n"

    email_action.send_message(zvt_config["email_username"], f"{current_timestamp} {entity_type}跌幅统计报告", msg)


if __name__ == "__main__":
    # from zvt.factors import VolumeUpMaFactor
    #
    # report_targets(factor_cls=VolumeUpMaFactor, entity_provider='joinquant', data_provider='joinquant', em_group='年线股票',
    #                title='放量突破(半)年线股票', entity_type='stock', em_group_over_write=True, filter_by_volume=True,
    #                adjust_type=AdjustType.hfq, start_timestamp='2019-01-01',
    #                # factor args
    #                windows=[120, 250], over_mode='or', up_intervals=50, turnover_threshold=400000000)
    report_top_stats(entity_type="stockhk", entity_provider="em", data_provider="em")
# the __all__ is generated
__all__ = ["report_targets"]
