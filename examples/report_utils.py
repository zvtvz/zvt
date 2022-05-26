# -*- coding: utf-8 -*-
import logging
import time
from typing import Type

from examples.utils import add_to_eastmoney
from zvt import zvt_config
from zvt.api import get_top_volume_entities, get_top_performance_entities, TopType
from zvt.api.kdata import get_latest_kdata_date, get_kdata_schema, default_adjust_type
from zvt.contract import IntervalLevel
from zvt.contract.api import get_entities, get_entity_schema, get_entity_ids
from zvt.contract.factor import Factor
from zvt.factors import TargetSelector, SelectMode
from zvt.informer import EmailInformer
from zvt.utils import next_date

logger = logging.getLogger("__name__")


def inform(
    action: EmailInformer, entity_ids, target_date, title, entity_provider, entity_type, em_group, em_group_over_write
):
    msg = "no targets"
    if entity_ids:
        entities = get_entities(
            provider=entity_provider, entity_type=entity_type, entity_ids=entity_ids, return_type="domain"
        )
        if em_group:
            try:
                codes = [entity.code for entity in entities]
                add_to_eastmoney(codes=codes, entity_type=entity_type, group=em_group, over_write=em_group_over_write)
            except Exception as e:
                action.send_message(
                    zvt_config["email_username"],
                    f"{target_date} {title} error",
                    f"{target_date} {title} error: {e}",
                )

        infos = [f"{entity.name}({entity.code})" for entity in entities]
        msg = "\n".join(infos) + "\n"
    logger.info(msg)
    action.send_message(zvt_config["email_username"], f"{target_date} {title}", msg)


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
            if not adjust_type:
                adjust_type = default_adjust_type(entity_type=entity_type)

            target_date = get_latest_kdata_date(
                provider=data_provider, entity_type=entity_type, adjust_type=adjust_type
            )
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
                    data_provider=data_provider,
                )
                current_entity_pool = vol_df.index.tolist()
                logger.info(f"current_entity_pool({len(current_entity_pool)}): {current_entity_pool}")

            kdata_schema = get_kdata_schema(entity_type, level=IntervalLevel.LEVEL_1DAY, adjust_type=adjust_type)
            filters = []
            if "turnover_threshold" in factor_kv:
                filters = filters + [kdata_schema.turnover >= factor_kv.get("turnover_threshold")]
            if "turnover_rate_threshold" in factor_kv:
                filters = filters + [kdata_schema.turnover_rate >= factor_kv.get("turnover_rate_threshold")]
            if filters:
                filters = filters + [kdata_schema.timestamp == target_date]
                kdata_df = kdata_schema.query_data(
                    provider=data_provider, filters=filters, columns=["entity_id", "timestamp"], index="entity_id"
                )
                if current_entity_pool:
                    current_entity_pool = set(current_entity_pool) & set(kdata_df.index.tolist())
                else:
                    current_entity_pool = kdata_df.index.tolist()

            if "entity_ids" in factor_kv:
                if current_entity_pool:
                    current_entity_pool = set(current_entity_pool) & set(factor_kv.pop("entity_ids"))
                else:
                    current_entity_pool = set(factor_kv.pop("entity_ids"))

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

            inform(
                email_action,
                entity_ids=long_stocks,
                target_date=target_date,
                title=title,
                entity_provider=entity_provider,
                entity_type=entity_type,
                em_group=em_group,
                em_group_over_write=em_group_over_write,
            )

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


def report_top_entities(
    entity_provider,
    data_provider,
    periods=None,
    ignore_new_stock=True,
    entity_type="stock",
    adjust_type=None,
    top_count=30,
    turnover_threshold=100000000,
    turnover_rate_threshold=0.02,
    em_group_over_write=True,
    return_type=TopType.positive,
):
    if periods is None:
        periods = [7, 30, 365]
    if not adjust_type:
        adjust_type = default_adjust_type(entity_type=entity_type)
    kdata_schema = get_kdata_schema(entity_type=entity_type, adjust_type=adjust_type)
    entity_schema = get_entity_schema(entity_type=entity_type)

    target_date = get_latest_kdata_date(provider=data_provider, entity_type=entity_type, adjust_type=adjust_type)
    email_action = EmailInformer()

    # 至少上市一年
    filter_entity_ids = []
    if ignore_new_stock:
        pre_year = next_date(target_date, -365)

        entity_ids = get_entity_ids(
            provider=entity_provider, entity_schema=entity_schema, filters=[entity_schema.timestamp <= pre_year]
        )

        if not entity_ids:
            msg = f"{entity_type} no entity_ids listed one year"
            logger.error(msg)
            email_action.send_message(zvt_config["email_username"], "report_top_stats error", msg)
            return
        filter_entity_ids = entity_ids

    filter_turnover_df = kdata_schema.query_data(
        filters=[
            kdata_schema.turnover >= turnover_threshold,
            kdata_schema.turnover_rate >= turnover_rate_threshold,
        ],
        provider=data_provider,
        start_timestamp=target_date,
        index="entity_id",
        columns=["entity_id", "code"],
    )
    if filter_entity_ids:
        filter_entity_ids = set(filter_entity_ids) & set(filter_turnover_df.index.tolist())
    else:
        filter_entity_ids = filter_turnover_df.index.tolist()

    if not filter_entity_ids:
        msg = f"{entity_type} no entity_ids selected"
        logger.error(msg)
        email_action.send_message(zvt_config["email_username"], "report_top_stats error", msg)
        return

    logger.info(f"{entity_type} filter_entity_ids size: {len(filter_entity_ids)}")
    filters = [kdata_schema.entity_id.in_(filter_entity_ids)]
    for i, period in enumerate(periods):
        start = next_date(target_date, -period)
        positive_df, negative_df = get_top_performance_entities(
            entity_type=entity_type,
            start_timestamp=start,
            filters=filters,
            pct=1,
            show_name=True,
            entity_provider=entity_provider,
            data_provider=data_provider,
            return_type=return_type,
        )

        if return_type == TopType.positive:
            tag = "最靓仔"
            df = positive_df
        else:
            tag = "谁有我惨"
            df = negative_df

        if i == 0:
            inform(
                email_action,
                entity_ids=df.index[:top_count].tolist(),
                target_date=target_date,
                title=f"{entity_type} {period}日内 {tag}",
                entity_provider=entity_provider,
                entity_type=entity_type,
                em_group=tag,
                em_group_over_write=em_group_over_write,
            )
        else:
            inform(
                email_action,
                entity_ids=df.index[:top_count].tolist(),
                target_date=target_date,
                title=f"{entity_type} {period}日内 {tag}",
                entity_provider=entity_provider,
                entity_type=entity_type,
                em_group=tag,
                em_group_over_write=False,
            )


if __name__ == "__main__":
    report_top_entities(
        entity_type="stockhk",
        entity_provider="em",
        data_provider="em",
        turnover_threshold=0,
        turnover_rate_threshold=0,
    )

# the __all__ is generated
__all__ = ["report_targets", "report_top_entities"]
