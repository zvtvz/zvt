# -*- coding: utf-8 -*-
import logging
import time
from typing import Type

from examples.tag_utils import group_stocks_by_tag, get_main_line_tags, get_main_line_hidden_tags
from examples.utils import msg_group_stocks_by_topic
from zvt import zvt_config
from zvt.api.kdata import get_latest_kdata_date, get_kdata_schema, default_adjust_type
from zvt.api.selector import get_limit_up_stocks
from zvt.api.stats import get_top_performance_entities_by_periods, get_top_volume_entities, TopType
from zvt.contract import IntervalLevel
from zvt.contract.api import get_entities, get_entity_schema
from zvt.contract.factor import Factor, TargetType
from zvt.domain import StockNews
from zvt.informer import EmailInformer
from zvt.informer.inform_utils import add_to_eastmoney
from zvt.utils.time_utils import date_time_by_interval

logger = logging.getLogger("__name__")


def inform(
    action: EmailInformer,
    entity_ids,
    target_date,
    title,
    entity_provider,
    entity_type,
    em_group,
    em_group_over_write,
    em_group_over_write_tag=False,
    group_by_topic=False,
    group_by_tag=True,
    special_hidden_tag="北交所",
):
    msg = "no targets"
    if entity_ids:
        entities = get_entities(
            provider=entity_provider, entity_type=entity_type, entity_ids=entity_ids, return_type="domain"
        )
        entities = [entity for entity in entities if entity.entity_id in entity_ids]
        print(len(entities))
        print(len(entity_ids))
        assert len(entities) == len(entity_ids)

        if group_by_topic and (entity_type == "stock"):
            StockNews.record_data(
                entity_ids=entity_ids,
                provider="em",
                force_update=False,
                sleeping_time=0.05,
                day_data=True,
            )

            msg = msg_group_stocks_by_topic(entities=entities, threshold=1, days_ago=60)
            logger.info(msg)
            action.send_message(zvt_config["email_username"], f"{target_date} {title}", msg)

        if group_by_tag and (entity_type == "stock"):
            main_line_hidden_tags = get_main_line_hidden_tags()
            sorted_entities = group_stocks_by_tag(
                entities=entities, hidden_tags=main_line_hidden_tags + [special_hidden_tag]
            )
            msg = ""
            main_line = []
            others = []
            special = []
            main_line_tags = get_main_line_tags()
            for index, (tag, stocks) in enumerate(sorted_entities):
                msg = msg + f"^^^^^^ {tag}[{len(stocks)}/{len(entities)}] ^^^^^^\n"
                msg = msg + "\n".join([f"{stock.name}({stock.code})" for stock in stocks]) + "\n"
                if tag == special_hidden_tag:
                    special = special + stocks
                elif (not main_line_tags) and (tag != "未知") and (index < 3):
                    main_line = main_line + stocks
                elif main_line_tags and (tag in main_line_tags):
                    main_line = main_line + stocks
                elif main_line_hidden_tags and (tag in main_line_hidden_tags):
                    main_line = main_line + stocks
                else:
                    others = others + stocks

            # 主线
            if main_line:
                codes = [entity.code for entity in main_line]
                add_to_eastmoney(codes=codes, entity_type=entity_type, group="主线", over_write=em_group_over_write_tag)

            # 其他
            if others:
                codes = [entity.code for entity in others]
                if not em_group:
                    em_group = "其他"
                add_to_eastmoney(codes=codes, entity_type=entity_type, group=em_group, over_write=em_group_over_write)
            # 特别处理
            if special:
                codes = [entity.code for entity in special]
                add_to_eastmoney(
                    codes=codes, entity_type=entity_type, group=special_hidden_tag, over_write=em_group_over_write_tag
                )
        else:
            if em_group:
                try:
                    codes = [entity.code for entity in entities]
                    add_to_eastmoney(
                        codes=codes, entity_type=entity_type, group=em_group, over_write=em_group_over_write
                    )
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
    informer: EmailInformer = None,
    em_group=None,
    em_group_over_write=True,
    em_group_over_write_tag=False,
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
                    start_timestamp=date_time_by_interval(target_date, -30),
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

            long_stocks = tech_factor.get_targets(timestamp=target_date, target_type=TargetType.positive)

            inform(
                informer,
                entity_ids=long_stocks,
                target_date=target_date,
                title=f"{entity_type} {title}({len(long_stocks)})",
                entity_provider=entity_provider,
                entity_type=entity_type,
                em_group=em_group,
                em_group_over_write=em_group_over_write,
                em_group_over_write_tag=em_group_over_write_tag,
            )

            break
        except Exception as e:
            logger.exception("report error:{}".format(e))
            time.sleep(60 * 3)
            error_count = error_count + 1
            if error_count == 10:
                informer.send_message(
                    zvt_config["email_username"],
                    f"report {entity_type}{factor_cls.__name__} error",
                    f"report {entity_type}{factor_cls.__name__} error: {e}",
                )


def report_top_entities(
    entity_provider,
    data_provider,
    periods=None,
    ignore_new_stock=True,
    ignore_st=True,
    entity_ids=None,
    entity_type="stock",
    adjust_type=None,
    top_count=30,
    turnover_threshold=100000000,
    turnover_rate_threshold=0.02,
    informer: EmailInformer = None,
    title="最强",
    em_group=None,
    em_group_over_write=True,
    em_group_over_write_tag=False,
    return_type=TopType.positive,
    include_limit_up=False,
):
    error_count = 0

    if not adjust_type:
        adjust_type = default_adjust_type(entity_type=entity_type)

    while error_count <= 10:
        try:
            target_date = get_latest_kdata_date(
                provider=data_provider, entity_type=entity_type, adjust_type=adjust_type
            )

            selected, real_period = get_top_performance_entities_by_periods(
                entity_provider=entity_provider,
                data_provider=data_provider,
                periods=periods,
                ignore_new_stock=ignore_new_stock,
                ignore_st=ignore_st,
                entity_ids=entity_ids,
                entity_type=entity_type,
                adjust_type=adjust_type,
                top_count=top_count,
                turnover_threshold=turnover_threshold,
                turnover_rate_threshold=turnover_rate_threshold,
                return_type=return_type,
            )

            if include_limit_up and (entity_type == "stock"):
                limit_up_stocks = get_limit_up_stocks(timestamp=target_date)
                if limit_up_stocks:
                    selected = list(set(selected + limit_up_stocks))

            inform(
                informer,
                entity_ids=selected,
                target_date=target_date,
                title=f"{entity_type} {title}({len(selected)})",
                entity_provider=entity_provider,
                entity_type=entity_type,
                em_group=em_group,
                em_group_over_write=em_group_over_write,
                em_group_over_write_tag=em_group_over_write_tag,
            )
            return real_period
        except Exception as e:
            logger.exception("report error:{}".format(e))
            time.sleep(30)
            error_count = error_count + 1


if __name__ == "__main__":
    report_top_entities(
        entity_type="block",
        entity_provider="em",
        data_provider="em",
        top_count=10,
        periods=[365, 750],
        ignore_new_stock=False,
        ignore_st=False,
        adjust_type=None,
        turnover_threshold=50000000,
        turnover_rate_threshold=0.005,
        em_group=None,
        em_group_over_write=False,
        return_type=TopType.negative,
    )

# the __all__ is generated
__all__ = ["report_targets", "report_top_entities"]
